from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.schemas.video import ProcessVideoRequest, ProcessVideoResponse, VideoJobResponse
from app.services.jobs import job_store
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
) -> ProcessVideoResponse:
    job = job_store.create(
        youtube_url=str(payload.youtube_url),
        transcript_text=payload.transcript_text,
    )
    await enqueue_video_job(job.job_id, background_tasks)
    return ProcessVideoResponse(
        job_id=job.job_id,
        status=job.status,
        estimated_time_seconds=15,
        poll_url=f"/api/videos/{job.job_id}",
    )


@router.get("/{job_id}", response_model=VideoJobResponse)
async def get_video_job(job_id: UUID) -> VideoJobResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video job not found")
    return job.to_response()
