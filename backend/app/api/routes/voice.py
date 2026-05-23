from uuid import uuid4

from fastapi import APIRouter, status

from app.schemas.voice import VoiceProfileRequest, VoiceProfileResponse
from app.services.voice import extract_voice_style

router = APIRouter()


@router.post("", response_model=VoiceProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_voice_profile(payload: VoiceProfileRequest) -> VoiceProfileResponse:
    return VoiceProfileResponse(
        id=uuid4(),
        name=payload.name,
        extracted_style=extract_voice_style(payload.samples),
    )
