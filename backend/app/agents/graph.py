from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel

from app.agents.nodes.analyzer import analyze_content
from app.agents.nodes.generators.blog import generate_blog
from app.agents.nodes.generators.carousel import generate_carousel
from app.agents.nodes.generators.linkedin import generate_linkedin
from app.agents.nodes.generators.newsletter import generate_newsletter
from app.agents.nodes.generators.shorts import generate_shorts
from app.agents.nodes.generators.twitter import generate_twitter
from app.agents.nodes.qa import QAResult, run_qa
from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import GeneratedContentKit
from app.schemas.transcript import Transcript
from app.schemas.voice import VoiceStyle
from app.services.transcript import TranscriptService


class PipelineResult(BaseModel):
    transcript: Transcript
    analysis: ContentAnalysis
    content: GeneratedContentKit
    qa: QAResult | None = None

    model_config = {"arbitrary_types_allowed": True}


def run_pipeline_for_transcript(
    transcript: Transcript,
    *,
    title: str | None = None,
    voice_style: VoiceStyle | None = None,
) -> PipelineResult:
    analysis = analyze_content(transcript, title=title)

    with ThreadPoolExecutor() as executor:
        future_twitter = executor.submit(generate_twitter, analysis, voice_style)
        future_linkedin = executor.submit(generate_linkedin, analysis, voice_style)
        future_newsletter = executor.submit(generate_newsletter, analysis, voice_style)
        future_blog = executor.submit(generate_blog, analysis, voice_style)
        future_shorts = executor.submit(generate_shorts, analysis, voice_style)
        future_carousel = executor.submit(generate_carousel, analysis, voice_style)

        content = GeneratedContentKit(
            twitter=future_twitter.result(),
            linkedin=future_linkedin.result(),
            newsletter=future_newsletter.result(),
            blog=future_blog.result(),
            shorts=future_shorts.result(),
            carousel=future_carousel.result(),
        )

    qa_result = run_qa(content, analysis, voice_style)

    return PipelineResult(
        transcript=transcript,
        analysis=analysis,
        content=qa_result.kit,
        qa=qa_result,
    )


def run_pipeline(youtube_url: str, transcript_service: TranscriptService | None = None) -> PipelineResult:
    service = transcript_service or TranscriptService()
    transcript = service.extract(youtube_url)
    return run_pipeline_for_transcript(transcript)
