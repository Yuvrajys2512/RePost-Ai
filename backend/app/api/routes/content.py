from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_user, get_db_session
from app.models.user import UserModel
from app.models.video import GeneratedContentModel

router = APIRouter()


@router.get("/{content_id}")
async def get_content(
    content_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    result = await db.execute(
        select(GeneratedContentModel)
        .options(selectinload(GeneratedContentModel.video_job))
        .where(GeneratedContentModel.id == str(content_id))
    )
    content = result.scalar_one_or_none()

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content piece not found",
        )

    # Verify that the requesting user owns the parent video job
    if content.video_job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this content piece",
        )

    return {
        "id": content.id,
        "video_job_id": content.video_job_id,
        "platform": content.platform,
        "payload": content.payload,
        "created_at": content.created_at,
    }


from pydantic import BaseModel

class VariationResponse(BaseModel):
    variations: list[str]


@router.post("/{content_id}/variations", response_model=VariationResponse)
async def get_content_variations(
    content_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> VariationResponse:
    # 1. Fetch content piece
    result = await db.execute(
        select(GeneratedContentModel)
        .options(selectinload(GeneratedContentModel.video_job))
        .where(GeneratedContentModel.id == str(content_id))
    )
    content = result.scalar_one_or_none()

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content piece not found",
        )

    # 2. Enforce strict ownership
    if content.video_job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this content piece",
        )

    p = content.platform.lower()
    
    # Platform-specific high impact A/B variations
    variations_map = {
        "twitter": [
            "The biggest bottleneck in standard content creation? Pacing. Here's a quick fix.",
            "Stop summarizing your videos. Try this storytelling framework instead:",
            "It took me 3 years to figure this out, but I'll break it down in 30 seconds."
        ],
        "linkedin": [
            "I spent 10 hours analyzing viral creators. They all do this one specific thing: they create a curiosity gap in the first line. Here's how to apply it.",
            "Surprising insight of the day: most startup editing is survivor bias. Here is the data from our latest test.",
            "A strong creator workflow isn't about working harder. It's about building a narrative loop. Let's deconstruct the framework."
        ],
        "newsletter": [
            "Subject: The storytelling framework nobody tells you about...",
            "Subject: I spent 3 years building the wrong loop. Here is why.",
            "Subject: Unpopular opinion: most creator advice is survivor bias."
        ],
        "blog": [
            "SEO Title: How to Scale Your Creative Output in 14 Days",
            "SEO Title: The Ultimate Guide to Storytelling Structure for Creators",
            "SEO Title: Stop Writing Generic AI Summaries: Try This Instead"
        ],
        "shorts": [
            "Hook Idea: This one editing mistake is costing you 90% of your retention.",
            "Hook Idea: Most creators think pacing is hard. It's not. Here is the trick.",
            "Hook Idea: In 14 days, we shipped 8 posts. Here is the process."
        ],
        "carousel": [
            "Headline: The 3-Step Storytelling Loop That Drives 10X Retention",
            "Headline: Why 90% of Creator Campaigns Fall Flat (And How to Fix It)",
            "Headline: How We Shipped 8 Posts From 2 Videos in 14 Days"
        ]
    }

    vars_list = variations_map.get(
        p,
        [
            "Alternative Option A: High impact headline hook",
            "Alternative Option B: Surprising curiosity gap hook",
            "Alternative Option C: Practical data-driven hook"
        ]
    )

    return VariationResponse(variations=vars_list)


class TrackEventRequest(BaseModel):
    action: str  # 'video_processed', 'content_copied', 'content_exported'
    platform: str | None = None


@router.post("/{content_id}/track")
async def track_content_event(
    content_id: UUID,
    payload: TrackEventRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    # 1. Fetch content piece
    result = await db.execute(
        select(GeneratedContentModel)
        .options(selectinload(GeneratedContentModel.video_job))
        .where(GeneratedContentModel.id == str(content_id))
    )
    content = result.scalar_one_or_none()

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content piece not found",
        )

    # 2. Enforce ownership
    if content.video_job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this content piece",
        )

    # 3. Create usage log
    from app.models.user import UsageLogModel
    log_entry = UsageLogModel(
        user_id=current_user.id,
        action=payload.action,
        platform=payload.platform or content.platform,
    )
    db.add(log_entry)
    await db.commit()

    return {"status": "success", "message": "Event tracked successfully"}

