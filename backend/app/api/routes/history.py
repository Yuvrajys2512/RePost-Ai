from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_user, get_db_session
from app.models.user import UserModel
from app.models.video import VideoJobModel
from app.services.jobs import map_model_to_response

router = APIRouter()


@router.get("")
async def get_history(
    page: int = 1,
    per_page: int = 20,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    # 1. Count total jobs for the current user
    count_result = await db.execute(
        select(func.count(VideoJobModel.id)).where(VideoJobModel.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    # 2. Fetch paginated video jobs with loaded content
    result = await db.execute(
        select(VideoJobModel)
        .options(selectinload(VideoJobModel.generated_content))
        .where(VideoJobModel.user_id == current_user.id)
        .order_by(VideoJobModel.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    jobs = result.scalars().all()

    return {
        "videos": [map_model_to_response(job) for job in jobs],
        "total": total,
        "page": page,
        "per_page": per_page,
    }
