from uuid import UUID, uuid4

from fastapi import APIRouter, status
from pydantic import AnyHttpUrl, BaseModel, Field

router = APIRouter()


class ProcessVideoRequest(BaseModel):
    youtube_url: AnyHttpUrl
    platforms: list[str] = Field(default_factory=lambda: ["twitter", "linkedin"])
    voice_profile_id: UUID | None = None


class ProcessVideoResponse(BaseModel):
    job_id: UUID
    status: str
    estimated_time_seconds: int
    poll_url: str


@router.post("/process", response_model=ProcessVideoResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_video(payload: ProcessVideoRequest) -> ProcessVideoResponse:
    job_id = uuid4()
    return ProcessVideoResponse(
        job_id=job_id,
        status="queued",
        estimated_time_seconds=60,
        poll_url=f"/api/videos/{job_id}",
    )


@router.get("/{job_id}")
async def get_video_job(job_id: UUID) -> dict:
    return {
        "job_id": job_id,
        "status": "queued",
        "status_detail": "foundation_stub",
        "progress": 0,
    }

