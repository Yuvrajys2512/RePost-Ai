from uuid import UUID

from pydantic import BaseModel, Field


class VoiceProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    samples: list[str] = Field(min_length=1)


class VoiceStyle(BaseModel):
    tone: str = Field(min_length=1)
    vocabulary: list[str] = Field(default_factory=list)
    sentence_length: str = Field(min_length=1)
    emoji_usage: str = Field(min_length=1)
    sample_count: int = Field(ge=1)


class VoiceProfileResponse(BaseModel):
    id: UUID
    name: str
    extracted_style: VoiceStyle

