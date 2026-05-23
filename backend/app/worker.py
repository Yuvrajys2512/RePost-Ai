from __future__ import annotations

from uuid import UUID

from arq.connections import RedisSettings

from app.config import get_settings
from app.services.jobs import process_video_job


async def process_video_pipeline(ctx: dict, job_id: str) -> None:
    process_video_job(UUID(job_id))


class WorkerSettings:
    functions = [process_video_pipeline]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)

