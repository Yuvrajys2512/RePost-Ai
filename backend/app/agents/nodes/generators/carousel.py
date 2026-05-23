from __future__ import annotations

from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import CarouselContent, CarouselSlide
from app.schemas.voice import VoiceStyle


def generate_carousel(
    analysis: ContentAnalysis, voice_style: VoiceStyle | None = None
) -> CarouselContent:
    caption_suffix = _voice_caption_suffix(analysis.audience_takeaway, voice_style)

    slides = [
        CarouselSlide(
            slide_number=1,
            headline=analysis.hook[:90],
            body="A strong carousel starts by making one specific promise.",
        )
    ]
    for idea in analysis.key_ideas[:6]:
        slides.append(
            CarouselSlide(
                slide_number=len(slides) + 1,
                headline=idea.title[:90],
                body=idea.summary[:220],
            )
        )
    slides.append(
        CarouselSlide(
            slide_number=len(slides) + 1,
            headline="The takeaway",
            body=analysis.audience_takeaway[:220],
        )
    )
    while len(slides) < 6:
        slides.insert(
            -1,
            CarouselSlide(
                slide_number=len(slides),
                headline="Make it specific",
                body="Specific ideas travel farther than broad summaries.",
            ),
        )
        for index, slide in enumerate(slides, start=1):
            slide.slide_number = index

    return CarouselContent(
        title=analysis.hook[:100],
        slides=slides[:10],
        caption=f"Save this if you want to repurpose videos without flattening the story. {caption_suffix}",
    )


def _voice_caption_suffix(takeaway: str, voice_style: VoiceStyle | None) -> str:
    if voice_style is None:
        return takeaway
    tone = voice_style.tone
    if tone == "direct and contrarian":
        return f"The honest version: {takeaway}"
    if tone == "practical and instructional":
        return f"Action step: {takeaway}"
    if tone == "reflective and narrative":
        return f"The lesson I keep sharing: {takeaway}"
    return takeaway
