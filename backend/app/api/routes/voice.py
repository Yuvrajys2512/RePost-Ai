from uuid import uuid4

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter()


class VoiceProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    samples: list[str] = Field(min_length=1)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_voice_profile(payload: VoiceProfileRequest) -> dict:
    return {
        "id": uuid4(),
        "name": payload.name,
        "extracted_style": {
            "tone": "pending-analysis",
            "sample_count": len(payload.samples),
        },
    }

