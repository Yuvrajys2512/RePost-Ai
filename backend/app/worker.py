from __future__ import annotations

from uuid import UUID

from arq.connections import RedisSettings

from app.config import get_settings
from app.services.jobs import process_video_job, process_video_job_db


async def process_video_pipeline(ctx: dict, job_id: str) -> None:
    process_video_job(UUID(job_id))


async def process_video_pipeline_db(ctx: dict, job_id: str) -> None:
    await process_video_job_db(job_id)


class WorkerSettings:
    functions = [process_video_pipeline, process_video_pipeline_db]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)

