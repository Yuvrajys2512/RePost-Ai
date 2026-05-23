from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import BackgroundTasks

from app.config import get_settings
from app.services.jobs import process_video_job, process_video_job_db


@dataclass(frozen=True)
class QueueDispatchResult:
    mode: str
    detail: str


async def enqueue_video_job(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    use_db: bool = False,
) -> QueueDispatchResult:
    settings = get_settings()
    
    if use_db:
        if not settings.use_redis_queue:
            background_tasks.add_task(process_video_job_db, str(job_id))
            return QueueDispatchResult(
                mode="background", detail="Queued in FastAPI background task (DB)"
            )

        try:
            redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
            await redis.enqueue_job("process_video_pipeline_db", str(job_id))
            await redis.close()
            return QueueDispatchResult(mode="redis", detail="Queued in Redis via ARQ (DB)")
        except Exception:
            background_tasks.add_task(process_video_job_db, str(job_id))
            return QueueDispatchResult(
                mode="background", detail="Queued in FastAPI background task (DB)"
            )
    else:
        if not settings.use_redis_queue:
            background_tasks.add_task(process_video_job, job_id)
            return QueueDispatchResult(
                mode="background", detail="Queued in FastAPI background task"
            )

        try:
            redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
            await redis.enqueue_job("process_video_pipeline", str(job_id))
            await redis.close()
            return QueueDispatchResult(mode="redis", detail="Queued in Redis via ARQ")
        except Exception:
            background_tasks.add_task(process_video_job, job_id)
            return QueueDispatchResult(
                mode="background", detail="Queued in FastAPI background task"
            )
