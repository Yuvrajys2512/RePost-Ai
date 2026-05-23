from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from threading import Lock
from uuid import UUID, uuid4

from pydantic import ValidationError

from app.agents.graph import run_pipeline_for_transcript
from app.schemas.generation import GeneratedContentKit
from app.schemas.video import VideoJobResponse, VideoJobStatus
from app.services.transcript import TranscriptExtractionError, TranscriptService, transcript_from_text


@dataclass
class VideoJob:
    job_id: UUID
    youtube_url: str
    status: VideoJobStatus
    status_detail: str
    progress: int
    created_at: datetime
    updated_at: datetime
    transcript_text: str | None = None
    content: GeneratedContentKit | None = None
    error: str | None = None

    def to_response(self) -> VideoJobResponse:
        return VideoJobResponse(
            job_id=self.job_id,
            status=self.status,
            status_detail=self.status_detail,
            progress=self.progress,
            created_at=self.created_at,
            updated_at=self.updated_at,
            youtube_url=self.youtube_url,
            content=self.content,
            error=self.error,
        )

    def to_record(self) -> dict:
        return {
            "job_id": str(self.job_id),
            "youtube_url": self.youtube_url,
            "status": self.status.value,
            "status_detail": self.status_detail,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "transcript_text": self.transcript_text,
            "content": self.content.model_dump(mode="json") if self.content else None,
            "error": self.error,
        }

    @classmethod
    def from_record(cls, record: dict) -> "VideoJob":
        content = None
        if record.get("content"):
            try:
                content = GeneratedContentKit.model_validate(record["content"])
            except ValidationError:
                content = None

        return cls(
            job_id=UUID(record["job_id"]),
            youtube_url=record["youtube_url"],
            status=VideoJobStatus(record["status"]),
            status_detail=record["status_detail"],
            progress=record["progress"],
            created_at=datetime.fromisoformat(record["created_at"]),
            updated_at=datetime.fromisoformat(record["updated_at"]),
            transcript_text=record.get("transcript_text"),
            content=content,
            error=record.get("error"),
        )


class LocalVideoJobStore:
    def __init__(self, path: Path | None = None) -> None:
        self._jobs: dict[UUID, VideoJob] = {}
        self._lock = Lock()
        self.path = path or Path(__file__).resolve().parents[2] / ".data" / "video_jobs.json"
        self._load()

    def create(self, youtube_url: str, transcript_text: str | None = None) -> VideoJob:
        now = datetime.now(UTC)
        job = VideoJob(
            job_id=uuid4(),
            youtube_url=youtube_url,
            transcript_text=transcript_text,
            status=VideoJobStatus.QUEUED,
            status_detail="Queued for transcript extraction",
            progress=0,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._load_unlocked()
            self._jobs[job.job_id] = job
            self._save_unlocked()
        return job

    def get(self, job_id: UUID) -> VideoJob | None:
        with self._lock:
            self._load_unlocked()
            return self._jobs.get(job_id)

    def update(self, job_id: UUID, **changes: object) -> VideoJob:
        with self._lock:
            self._load_unlocked()
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)
            job.updated_at = datetime.now(UTC)
            self._save_unlocked()
            return job

    def _load(self) -> None:
        with self._lock:
            self._load_unlocked()

    def _load_unlocked(self) -> None:
        if not self.path.exists():
            self._jobs = {}
            return
        records = json.loads(self.path.read_text(encoding="utf-8"))
        self._jobs = {
            UUID(record["job_id"]): VideoJob.from_record(record)
            for record in records
        }

    def _save_unlocked(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        records = [job.to_record() for job in self._jobs.values()]
        self.path.write_text(json.dumps(records, indent=2), encoding="utf-8")


job_store = LocalVideoJobStore()


def process_video_job(job_id: UUID, store: LocalVideoJobStore = job_store) -> None:
    job = store.get(job_id)
    if job is None:
        return

    try:
        store.update(
            job_id,
            status=VideoJobStatus.PROCESSING,
            status_detail="Extracting transcript",
            progress=25,
        )
        transcript = _load_transcript(job.youtube_url, job.transcript_text)

        store.update(job_id, status_detail="Analyzing content", progress=55)
        result = run_pipeline_for_transcript(transcript)

        store.update(job_id, status_detail="Generating platform content", progress=85)
        store.update(
            job_id,
            status=VideoJobStatus.COMPLETED,
            status_detail="Content kit ready",
            progress=100,
            content=result.content,
        )
    except Exception as exc:
        store.update(
            job_id,
            status=VideoJobStatus.FAILED,
            status_detail="Pipeline failed",
            progress=100,
            error=str(exc),
        )


def _load_transcript(youtube_url: str, transcript_text: str | None):
    if transcript_text:
        return transcript_from_text(transcript_text, video_id="manual", source_url=youtube_url)

    try:
        return TranscriptService().extract(youtube_url)
    except TranscriptExtractionError:
        fallback_text = (
            "Transcript extraction is not configured in this local environment. "
            "This Phase 2 demo keeps the API and frontend contract live by generating "
            "sample content from the submitted YouTube URL. "
            f"The submitted URL was {youtube_url}. "
            "Install the transcript extra to replace this fallback with the real video transcript."
        )
        return transcript_from_text(fallback_text, video_id="fallback", source_url=youtube_url)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
