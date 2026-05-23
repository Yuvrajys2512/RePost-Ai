from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_user, get_db_session
from app.models.user import UserModel
from app.models.video import VideoJobModel
from app.schemas.video import ProcessVideoRequest, ProcessVideoResponse, VideoJobResponse, VideoJobStatus
from app.services.jobs import map_model_to_response
from app.services.quota import has_remaining_quota
from app.services.queue import enqueue_video_job

router = APIRouter()


@router.post(
    "/process",
    response_model=ProcessVideoResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_video(
    payload: ProcessVideoRequest,
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ProcessVideoResponse:
    # 1. Enforce monthly subscription quotas
    if not has_remaining_quota(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Monthly video processing limit reached. Please upgrade your plan in the Billing tab.",
        )

    # 2. Persist the new Video Job record associated with the user
    job = VideoJobModel(
        user_id=current_user.id,
        youtube_url=str(payload.youtube_url),
        transcript_text=payload.transcript_text,
        status=VideoJobStatus.QUEUED.value,
        status_detail="Queued for transcript extraction",
        progress=0,
    )
    db.add(job)

    # 3. Track and increment the monthly usage counter
    current_user.videos_used_this_month += 1
    
    await db.commit()
    await db.refresh(job)

    # 4. Dispatch the job asynchronously
    await enqueue_video_job(UUID(job.id), background_tasks, use_db=True)

    return ProcessVideoResponse(
        job_id=UUID(job.id),
        status=VideoJobStatus(job.status),
        estimated_time_seconds=15,
        poll_url=f"/api/videos/{job.id}",
    )


@router.get("/{job_id}", response_model=VideoJobResponse)
async def get_video_job(
    job_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> VideoJobResponse:
    # Fetch job with preloaded generated content pieces
    result = await db.execute(
        select(VideoJobModel)
        .options(selectinload(VideoJobModel.generated_content))
        .where(VideoJobModel.id == str(job_id))
    )
    job = result.scalar_one_or_none()
    
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Video job not found",
        )
        
    # Enforce strict user isolation
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this video job",
        )

    return map_model_to_response(job)
