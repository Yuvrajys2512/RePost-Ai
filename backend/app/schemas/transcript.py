from pydantic import BaseModel, Field, computed_field


class TranscriptSegment(BaseModel):
    start_seconds: float = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    text: str = Field(min_length=1)


class Transcript(BaseModel):
    video_id: str = Field(min_length=1)
    source_url: str
    language: str = Field(default="en", min_length=2, max_length=16)
    segments: list[TranscriptSegment] = Field(min_length=1)

    @computed_field
    @property
    def text(self) -> str:
        return " ".join(segment.text.strip() for segment in self.segments if segment.text.strip())

    @computed_field
    @property
    def duration_seconds(self) -> float:
        return max(
            segment.start_seconds + segment.duration_seconds
            for segment in self.segments
        )

