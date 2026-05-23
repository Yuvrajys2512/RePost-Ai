from __future__ import annotations

from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import BlogContent, BlogSection
from app.schemas.voice import VoiceStyle


def generate_blog(
    analysis: ContentAnalysis, voice_style: VoiceStyle | None = None
) -> BlogContent:
    sections = [
        BlogSection(
            heading=idea.title,
            body=(
                f"{idea.summary} This works because the point is specific enough to become "
                f"a reusable content angle instead of a generic summary."
            ),
        )
        for idea in analysis.key_ideas[:4]
    ]
    while len(sections) < 3:
        sections.append(
            BlogSection(
                heading="What creators should do next",
                body=analysis.audience_takeaway,
            )
        )

    # Apply voice-specific intro sentence if available
    intro_prefix = _voice_intro(voice_style)

    return BlogContent(
        title=(analysis.title or analysis.hook)[:120],
        meta_description=analysis.summary[:160],
        introduction=(
            f"{intro_prefix}{analysis.summary} The real value is in translating that structure into "
            f"platform-native content."
        ),
        sections=sections,
        conclusion=f"Bottom line: {analysis.audience_takeaway}",
    )


def _voice_intro(voice_style: VoiceStyle | None) -> str:
    if voice_style is None:
        return ""
    tone = voice_style.tone
    if tone == "direct and contrarian":
        return "Most people get this wrong. "
    if tone == "practical and instructional":
        return "Here's a framework worth understanding. "
    if tone == "reflective and narrative":
        return "This took me a while to figure out. "
    return ""
