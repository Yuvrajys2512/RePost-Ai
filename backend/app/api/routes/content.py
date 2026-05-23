from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_user, get_db_session
from app.models.user import UserModel
from app.models.video import GeneratedContentModel

router = APIRouter()


@router.get("/{content_id}")
async def get_content(
    content_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    result = await db.execute(
        select(GeneratedContentModel)
        .options(selectinload(GeneratedContentModel.video_job))
        .where(GeneratedContentModel.id == str(content_id))
    )
    content = result.scalar_one_or_none()

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content piece not found",
        )

    # Verify that the requesting user owns the parent video job
    if content.video_job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this content piece",
        )

    return {
        "id": content.id,
        "video_job_id": content.video_job_id,
        "platform": content.platform,
        "payload": content.payload,
        "created_at": content.created_at,
    }
