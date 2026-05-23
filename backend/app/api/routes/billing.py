from datetime import UTC, datetime
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_current_user, get_db_session
from app.models.user import UserModel

router = APIRouter()


@router.get("/user")
async def get_user_profile(
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    return {
        "id": current_user.id,
        "email": current_user.email,
        "plan": current_user.plan,
        "videos_used_this_month": current_user.videos_used_this_month,
        "billing_cycle_start": current_user.billing_cycle_start,
    }


class CheckoutRequest(BaseModel):
    plan: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class MockChargeRequest(BaseModel):
    plan: str


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    payload: CheckoutRequest,
    current_user: UserModel = Depends(get_current_user),
) -> CheckoutResponse:
    settings = get_settings()
    plan_name = payload.plan.lower()

    if plan_name not in ["starter", "pro", "agency"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan selection. Choose starter, pro, or agency.",
        )

    # If credentials are not set, return a mock developer checkout trigger
    if not settings.lemon_squeezy_api_key:
        return CheckoutResponse(
            checkout_url=f"http://localhost:3000?mock-upgrade={plan_name}"
        )

    # In production/live mode, return Lemon Squeezy checkout URL mapped to variants
    # (Using user.id passed in custom_data so webhook maps back successfully)
    checkout_url = (
        f"https://repost-ai.lemonsqueezy.com/checkout/buy/{plan_name}-plan"
        f"?checkout[custom][user_id]={current_user.id}"
        f"&checkout[email]={current_user.email}"
    )
    return CheckoutResponse(checkout_url=checkout_url)


@router.post("/mock-charge")
async def mock_charge(
    payload: MockChargeRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    plan_name = payload.plan.lower()
    if plan_name not in ["free", "starter", "pro", "agency"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan name for simulation",
        )

    # Simulate paid plan upgrade
    current_user.plan = plan_name
    current_user.videos_used_this_month = 0
    current_user.billing_cycle_start = datetime.now(UTC)

    await db.commit()
    await db.refresh(current_user)

    return {
        "status": "success",
        "message": f"Successfully simulated payment upgrade to {plan_name}",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "plan": current_user.plan,
            "videos_used_this_month": current_user.videos_used_this_month,
        },
    }


@router.post("/webhook")
async def billing_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    settings = get_settings()
    body = await request.body()

    # Verify signature if webhook secret is configured
    if settings.lemon_squeezy_webhook_secret:
        import hmac
        import hashlib
        signature = request.headers.get("X-Signature")
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature",
            )
        digest = hmac.new(
            settings.lemon_squeezy_webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(digest, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    import json
    try:
        data = json.loads(body.decode())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    meta = data.get("meta", {})
    event_name = meta.get("event_name")
    
    # Check custom_data passed in checkout
    custom_data = meta.get("custom_data", {})
    user_id = custom_data.get("user_id")

    if not user_id:
        # Ignore events without matching user mapping
        return {"status": "ignored", "reason": "Missing user_id custom metadata"}

    # Fetch user from local DB
    from sqlalchemy import select
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found in database",
        )

    attributes = data.get("data", {}).get("attributes", {})
    variant_name = attributes.get("variant_name", "").lower()

    if event_name in ["subscription_created", "subscription_updated"]:
        # Map variant_name or variant_id to our plans
        if "starter" in variant_name:
            user.plan = "starter"
        elif "agency" in variant_name:
            user.plan = "agency"
        else:
            user.plan = "pro"
            
        user.videos_used_this_month = 0
        user.billing_cycle_start = datetime.now(UTC)
        await db.commit()

    elif event_name == "subscription_cancelled":
        # Cancelled subscriptions revert to free tier at end of billing cycle
        user.plan = "free"
        await db.commit()

    return {"status": "success", "event": event_name, "user_id": user_id, "active_plan": user.plan}


class CreateApiKeyRequest(BaseModel):
    name: str


@router.get("/keys")
async def list_api_keys(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    # Gated: Only Agency plan can use this (or we let anyone view, but they can't generate)
    # The requirement specifies: Developer API Keys provisioning gated for the Agency tier.
    # Let's enforce that both listing and generating requires Agency plan
    if current_user.plan != "agency":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key management is restricted to the Agency tier. Please upgrade.",
        )

    from sqlalchemy import select
    from app.models.user import ApiKeyModel
    result = await db.execute(
        select(ApiKeyModel)
        .where(ApiKeyModel.user_id == current_user.id)
        .order_by(ApiKeyModel.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        {
            "id": k.id,
            "name": k.name,
            "key_value": k.key_value,
            "created_at": k.created_at,
        }
        for k in keys
    ]


@router.post("/keys")
async def create_api_key(
    payload: CreateApiKeyRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    if current_user.plan != "agency":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Developer API Keys are only available on the Agency tier. Please upgrade your plan.",
        )

    import secrets
    from app.models.user import ApiKeyModel

    key_value = f"rp_live_{secrets.token_hex(24)}"
    new_key = ApiKeyModel(
        user_id=current_user.id,
        key_value=key_value,
        name=payload.name,
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return {
        "status": "success",
        "key": {
            "id": new_key.id,
            "name": new_key.name,
            "key_value": new_key.key_value,
            "created_at": new_key.created_at,
        }
    }


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    if current_user.plan != "agency":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key management is restricted to the Agency tier.",
        )

    from sqlalchemy import select
    from app.models.user import ApiKeyModel
    result = await db.execute(
        select(ApiKeyModel)
        .where(ApiKeyModel.id == key_id, ApiKeyModel.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found or does not belong to you",
        )
    await db.delete(api_key)
    await db.commit()

    return {"status": "success", "message": "API key revoked successfully"}

