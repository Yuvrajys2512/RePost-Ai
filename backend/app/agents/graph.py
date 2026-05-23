from __future__ import annotations

from pydantic import BaseModel

from app.agents.nodes.analyzer import analyze_content
from app.agents.nodes.generators.linkedin import generate_linkedin
from app.agents.nodes.generators.twitter import generate_twitter
from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import GeneratedContentKit
from app.schemas.transcript import Transcript
from app.services.transcript import TranscriptService


class PipelineResult(BaseModel):
    transcript: Transcript
    analysis: ContentAnalysis
    content: GeneratedContentKit


def run_pipeline_for_transcript(transcript: Transcript, *, title: str | None = None) -> PipelineResult:
    analysis = analyze_content(transcript, title=title)
    content = GeneratedContentKit(
        twitter=generate_twitter(analysis),
        linkedin=generate_linkedin(analysis),
    )
    return PipelineResult(transcript=transcript, analysis=analysis, content=content)


def run_pipeline(youtube_url: str, transcript_service: TranscriptService | None = None) -> PipelineResult:
    service = transcript_service or TranscriptService()
    transcript = service.extract(youtube_url)
    return run_pipeline_for_transcript(transcript)

