from uuid import UUID

from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_user, get_db_session
from app.models.user import UserModel
from app.models.video import GeneratedContentModel, VideoJobModel
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
        voice_profile_id=str(payload.voice_profile_id) if payload.voice_profile_id else None,
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


class RegenerateRequest(BaseModel):
    platform: str


@router.post("/{job_id}/regenerate")
async def regenerate_platform_content(
    job_id: UUID,
    payload: RegenerateRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    from datetime import UTC, datetime
    from sqlalchemy import delete
    
    # 1. Fetch the video job
    result = await db.execute(
        select(VideoJobModel).where(VideoJobModel.id == str(job_id))
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video job not found")

    # 2. Verify job ownership
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this video job",
        )

    platform_name = payload.platform.lower()
    if platform_name not in ["twitter", "linkedin", "newsletter", "blog", "shorts", "carousel"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid platform selection",
        )

    try:
        # 3. Extract transcript
        from app.services.jobs import _load_transcript
        transcript = _load_transcript(job.youtube_url, job.transcript_text)

        # 4. Re-run Platform Generator Nodes
        from app.agents.nodes.analyzer import analyze_content
        from app.agents.nodes.generators.blog import generate_blog
        from app.agents.nodes.generators.carousel import generate_carousel
        from app.agents.nodes.generators.linkedin import generate_linkedin
        from app.agents.nodes.generators.newsletter import generate_newsletter
        from app.agents.nodes.generators.shorts import generate_shorts
        from app.agents.nodes.generators.twitter import generate_twitter

        analysis = analyze_content(transcript)

        if platform_name == "twitter":
            new_copy = generate_twitter(analysis)
        elif platform_name == "linkedin":
            new_copy = generate_linkedin(analysis)
        elif platform_name == "newsletter":
            new_copy = generate_newsletter(analysis)
        elif platform_name == "blog":
            new_copy = generate_blog(analysis)
        elif platform_name == "shorts":
            new_copy = generate_shorts(analysis)
        else:
            new_copy = generate_carousel(analysis)

        # 5. Clear old copy from the database
        await db.execute(
            delete(GeneratedContentModel)
            .where(GeneratedContentModel.video_job_id == job.id)
            .where(GeneratedContentModel.platform == platform_name)
        )

        # 6. Insert new regenerated platform copy
        content_row = GeneratedContentModel(
            video_job_id=job.id,
            platform=platform_name,
            payload=new_copy.model_dump(mode="json"),
        )
        db.add(content_row)

        job.updated_at = datetime.now(UTC)
        await db.commit()

        return {
            "status": "success",
            "platform": platform_name,
            "payload": content_row.payload,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Regeneration pipeline failed: {str(exc)}",
        )
