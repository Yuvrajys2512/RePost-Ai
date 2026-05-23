from __future__ import annotations

from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import ShortsClip, ShortsContent
from app.schemas.voice import VoiceStyle


def generate_shorts(
    analysis: ContentAnalysis, voice_style: VoiceStyle | None = None
) -> ShortsContent:
    script_suffix = _voice_close(analysis.audience_takeaway, voice_style)

    clips = []
    for index, idea in enumerate(analysis.key_ideas[:5]):
        start = float(index * 45)
        clips.append(
            ShortsClip(
                title=idea.title[:100],
                start_seconds=start,
                end_seconds=start + 35.0,
                hook=idea.summary[:220],
                script=(
                    f"Open with: {idea.summary} Then show why it matters, give one concrete "
                    f"example, and close with: {script_suffix}"
                ),
            )
        )
    while len(clips) < 3:
        start = float(len(clips) * 45)
        clips.append(
            ShortsClip(
                title="Core takeaway",
                start_seconds=start,
                end_seconds=start + 35.0,
                hook=analysis.hook[:220],
                script=f"Use the hook, explain the tension, and land on {script_suffix}",
            )
        )
    return ShortsContent(clips=clips)


def _voice_close(takeaway: str, voice_style: VoiceStyle | None) -> str:
    if voice_style is None:
        return takeaway
    tone = voice_style.tone
    if tone == "direct and contrarian":
        return f"Here's the truth: {takeaway}"
    if tone == "practical and instructional":
        return f"Try this: {takeaway}"
    if tone == "reflective and narrative":
        return f"Looking back, it comes down to this: {takeaway}"
    return takeaway
