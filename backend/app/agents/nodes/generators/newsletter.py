from __future__ import annotations

from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import NewsletterContent
from app.schemas.voice import VoiceStyle


def generate_newsletter(
    analysis: ContentAnalysis, voice_style: VoiceStyle | None = None
) -> NewsletterContent:
    first_idea = analysis.key_ideas[0]
    subject_seed = first_idea.title[:42].rstrip()

    # Tone-adapted opening line
    opener = _tone_opener(analysis.hook, voice_style)

    body = (
        f"{opener}\n\n"
        f"The important idea is this: {first_idea.summary}\n\n"
        f"The structure matters because the video does not just list information. It creates "
        f"a hook, gives the audience a reason to care, and turns the insight into a practical "
        f"next step.\n\n"
        f"{analysis.audience_takeaway}"
    )

    return NewsletterContent(
        subject_lines=[
            f"The mistake behind {subject_seed}",
            f"A sharper way to use {subject_seed}",
            "Turn one video into better ideas",
        ],
        preview_text=analysis.audience_takeaway[:180],
        body=body,
        cta="Watch the full video and look for the hook, tension, insight, and payoff.",
    )


def _tone_opener(hook: str, voice_style: VoiceStyle | None) -> str:
    if voice_style is None:
        return hook
    tone = voice_style.tone
    if tone == "direct and contrarian":
        return f"Let me be direct: {hook}"
    if tone == "practical and instructional":
        return f"Here's something practical worth knowing: {hook}"
    if tone == "reflective and narrative":
        return f"Something I keep coming back to: {hook}"
    return hook
