from typing import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.config import get_settings
from app.db import session as _session_module
from app.models.user import UserModel


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _session_module.AsyncSessionLocal() as session:
        yield session


async def get_or_create_user(db: AsyncSession, user_id: str, email: str | None = None) -> UserModel:
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        user = UserModel(
            id=user_id,
            email=email or f"user_{user_id[:8]}@example.com",
            plan="free",
            videos_used_this_month=0,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def get_current_user(
    authorization: str | None = Header(None),
    x_api_key: str | None = Header(None),
    db: AsyncSession = Depends(get_db_session),
) -> UserModel:
    # 1. First, check if X-API-Key is provided in headers
    if x_api_key:
        from app.models.user import ApiKeyModel
        result = await db.execute(
            select(UserModel)
            .join(ApiKeyModel, UserModel.id == ApiKeyModel.user_id)
            .where(ApiKeyModel.key_value == x_api_key)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        if user.plan != "agency":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API access is restricted to the Agency tier. Please upgrade your plan.",
            )
        return user

    # 2. Revert to standard Authorization Bearer Token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization credentials",
        )
    token = authorization.split(" ")[1]

    settings = get_settings()

    # Developer Mock Authentication Mode
    if token == "mock-user-token" or not settings.supabase_jwt_secret:
        mock_id = "00000000-0000-0000-0000-000000000000"
        mock_email = "mock@repost.ai"
        return await get_or_create_user(db, mock_id, mock_email)

    # Standard Supabase JWT Authentication
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": True},
            audience="authenticated",
        )
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing user identifier",
            )
        return await get_or_create_user(db, user_id, email)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication token verification failed: {str(exc)}",
        )

