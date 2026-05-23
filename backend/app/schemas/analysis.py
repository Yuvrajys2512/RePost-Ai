from pydantic import BaseModel, Field


class ContentIdea(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)


class StoryBeat(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1)


class ContentAnalysis(BaseModel):
    video_id: str = Field(min_length=1)
    title: str | None = None
    summary: str = Field(min_length=1)
    hook: str = Field(min_length=1)
    key_ideas: list[ContentIdea] = Field(min_length=1)
    quotes: list[str] = Field(default_factory=list)
    data_points: list[str] = Field(default_factory=list)
    emotional_beats: list[str] = Field(default_factory=list)
    story_structure: list[StoryBeat] = Field(min_length=1)
    audience_takeaway: str = Field(min_length=1)

