from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field

from app.schemas.generation import GeneratedContentKit, Platform


class VideoJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessVideoRequest(BaseModel):
    youtube_url: AnyHttpUrl
    platforms: list[Platform] = Field(default_factory=lambda: [Platform.TWITTER, Platform.LINKEDIN])
    voice_profile_id: UUID | None = None
    transcript_text: str | None = Field(default=None, min_length=1)


class ProcessVideoResponse(BaseModel):
    job_id: UUID
    status: VideoJobStatus
    estimated_time_seconds: int
    poll_url: str


class VideoJobResponse(BaseModel):
    job_id: UUID
    status: VideoJobStatus
    status_detail: str
    progress: int = Field(ge=0, le=100)
    created_at: datetime
    updated_at: datetime
    youtube_url: str
    content: GeneratedContentKit | None = None
    content_ids: dict[str, str] | None = None
    error: str | None = None


