from __future__ import annotations

from app.agents.llm import call_llm_json, has_llm_provider
from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import ShortsClip, ShortsContent
from app.schemas.voice import VoiceStyle

_SYSTEM_PROMPT = """\
You are a world-class YouTube Shorts strategist and scriptwriter for YouTube creators.

You take a content analysis of a YouTube video and identify 3-5 moments that would
make exceptional 30-45 second Shorts — and write the scripts for them.

RULES:
- Each Short must stand completely alone. Viewers don't need context from the main video.
- Hook is everything. The first 3 seconds determines if someone swipes. Make it a bold claim,
  a surprising fact, or a question that creates immediate tension. Under 220 characters.
- Scripts follow this structure: Hook → 1 tight example or proof → Payoff/CTA.
  No fluff. Every word earns its place. 30-45 seconds of spoken audio.
- Titles: what the Short is about in plain language. Not "Part 3" or "Clip 4". Under 100 chars.
- Find genuinely different moments — don't extract 5 versions of the same idea.
  Cover different angles: a strong claim, a counterintuitive insight, a practical tip,
  a surprising fact, a personal story beat.
- If a voice profile is provided, match the creator's rhythm and vocabulary in the scripts.\
"""


def generate_shorts(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
) -> ShortsContent:
    if has_llm_provider():
        try:
            return _generate_with_llm(analysis, voice_style)
        except Exception:
            pass
    return _generate_deterministic(analysis, voice_style)


def _generate_with_llm(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None,
) -> ShortsContent:
    user_message = _build_user_message(analysis, voice_style)
    data = call_llm_json(_SYSTEM_PROMPT, user_message, temperature=0.7)

    raw_clips = data.get("clips", [])
    clips: list[ShortsClip] = []
    for i, c in enumerate(raw_clips[:5]):
        title = (c.get("title") or "").strip()[:100]
        hook = (c.get("hook") or "").strip()[:220]
        script = (c.get("script") or "").strip()
        if not title or not hook or not script:
            continue
        start = float(i * 50)
        clips.append(
            ShortsClip(
                title=title,
                start_seconds=start,
                end_seconds=start + 40.0,
                hook=hook,
                script=script,
            )
        )

    if len(clips) < 3:
        return _generate_deterministic(analysis, voice_style)

    return ShortsContent(clips=clips[:5])


def _build_user_message(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None,
) -> str:
    ideas = "\n".join(
        f"  - {idea.title}: {idea.summary}"
        + (f"\n    Quote: \"{idea.evidence[0]}\"" if idea.evidence else "")
        for idea in analysis.key_ideas
    )
    quotes = "\n".join(f"  - \"{q}\"" for q in analysis.quotes) or "  (none)"
    data_points = "\n".join(f"  - {d}" for d in analysis.data_points) or "  (none)"
    beats = "\n".join(f"  - {b}" for b in analysis.emotional_beats) or "  (none)"

    voice_section = ""
    if voice_style:
        vocab = ", ".join(voice_style.vocabulary[:6]) if voice_style.vocabulary else "none listed"
        voice_section = (
            f"\nCreator voice profile:\n"
            f"  Tone: {voice_style.tone}\n"
            f"  Sentence length: {voice_style.sentence_length}\n"
            f"  Emoji usage: {voice_style.emoji_usage}\n"
            f"  Vocabulary style: {vocab}\n"
        )

    return f"""\
Video: {analysis.title or "Untitled"}

Hook: {analysis.hook}
Core summary: {analysis.summary}
Audience takeaway: {analysis.audience_takeaway}

Key ideas:
{ideas}

Quotable lines:
{quotes}

Data points:
{data_points}

Emotional beats:
{beats}
{voice_section}
Identify 3-5 moments for YouTube Shorts from this video. Return JSON exactly like this:
{{
  "clips": [
    {{
      "title": "short title under 100 chars",
      "hook": "opening line under 220 chars — makes someone stop scrolling in 3 seconds",
      "script": "full 30-45 second script: hook, one proof or example, payoff/CTA"
    }}
  ]
}}

Each clip must stand alone without the main video. Cover different angles.\
"""


# ---------------------------------------------------------------------------
# Deterministic fallback — used when no LLM provider is configured (tests)
# ---------------------------------------------------------------------------


def _generate_deterministic(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
) -> ShortsContent:
    script_suffix = _voice_close(analysis.audience_takeaway, voice_style)

    clips = []
    for index, idea in enumerate(analysis.key_ideas[:5]):
        start = float(index * 50)
        clips.append(
            ShortsClip(
                title=idea.title[:100],
                start_seconds=start,
                end_seconds=start + 40.0,
                hook=idea.summary[:220],
                script=(
                    f"Open with: {idea.summary} Then show why it matters, give one concrete "
                    f"example, and close with: {script_suffix}"
                ),
            )
        )
    while len(clips) < 3:
        start = float(len(clips) * 50)
        clips.append(
            ShortsClip(
                title="Core takeaway",
                start_seconds=start,
                end_seconds=start + 40.0,
                hook=analysis.hook[:220],
                script=f"Use the hook, explain the tension, and land on: {script_suffix}",
            )
        )
    return ShortsContent(clips=clips[:5])


def _voice_close(takeaway: str, voice_style: VoiceStyle | None) -> str:
    if voice_style is None:
        return takeaway
    tone = voice_style.tone
    if "contrarian" in tone:
        return f"Here's the truth: {takeaway}"
    if "practical" in tone or "instructional" in tone:
        return f"Try this: {takeaway}"
    if "reflective" in tone or "narrative" in tone:
        return f"Looking back, it comes down to this: {takeaway}"
    return takeaway
