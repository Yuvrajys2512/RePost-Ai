from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.models.user import UserModel, UsageLogModel
from app.models.video import VideoJobModel

router = APIRouter()


@router.get("")
async def get_analytics(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    # 1. Get total video runs converted
    result_jobs = await db.execute(
        select(VideoJobModel).where(VideoJobModel.user_id == current_user.id)
    )
    jobs = result_jobs.scalars().all()
    total_runs = len(jobs)

    # 2. Get usage logs to calculate platform distribution and recent activity
    result_logs = await db.execute(
        select(UsageLogModel)
        .where(UsageLogModel.user_id == current_user.id)
        .order_by(UsageLogModel.created_at.desc())
    )
    logs = result_logs.scalars().all()

    # Calculate platform copy/export distribution
    # Let's count platforms for copy and export actions
    platform_distribution = {}
    for log in logs:
        if log.action in ["content_copied", "content_exported"] and log.platform:
            p = log.platform.lower()
            platform_distribution[p] = platform_distribution.get(p, 0) + 1

    # Format recent activity logs (limit to 10 for dashboard display)
    recent_activity = []
    for log in logs[:10]:
        recent_activity.append({
            "id": log.id,
            "action": log.action,
            "platform": log.platform,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })

    return {
        "total_runs": total_runs,
        "platform_distribution": platform_distribution,
        "recent_activity": recent_activity,
    }
