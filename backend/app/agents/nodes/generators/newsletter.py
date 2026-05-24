from __future__ import annotations

from app.agents.llm import call_llm_json, has_llm_provider
from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import NewsletterContent
from app.schemas.voice import VoiceStyle

_SYSTEM_PROMPT = """\
You are a world-class email newsletter ghostwriter for YouTube creators.

You take a content analysis of a YouTube video and write an email newsletter that the
CREATOR THEMSELVES would send to their audience — in their voice, as their own writing.

RULES:
- Write AS the creator. First person: "I", "my", "we". Always.
- Never write "The creator" or "They explain". You are writing what THEY would send.
- The subject lines must be specific to THIS video — a subscriber who sees the subject
  must feel it was written just for them. Generic subjects like "This week's video" are failures.
- Preview text should tease the email without giving away the punchline.
- Body: 200-350 words. Short paragraphs. One idea per paragraph. White space matters.
  Open with why this video mattered to you personally, then give the 2-3 sharpest insights,
  then land on the practical takeaway. No listicles. Prose.
- CTA: One clear action. Link to the video or invite a reply. Under 220 characters.
- If a voice profile is provided, match the creator's tone, sentence rhythm, and vocabulary.\
"""


def generate_newsletter(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
) -> NewsletterContent:
    if has_llm_provider():
        try:
            return _generate_with_llm(analysis, voice_style)
        except Exception:
            pass
    return _generate_deterministic(analysis, voice_style)


def _generate_with_llm(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None,
) -> NewsletterContent:
    user_message = _build_user_message(analysis, voice_style)
    data = call_llm_json(_SYSTEM_PROMPT, user_message, temperature=0.65)

    subject_lines = [s.strip() for s in data.get("subject_lines", []) if s.strip()]
    preview_text = (data.get("preview_text") or "").strip()[:180]
    body = (data.get("body") or "").strip()
    cta = (data.get("cta") or "").strip()[:220]

    # Fall back to deterministic if LLM response is missing required fields
    if len(subject_lines) < 3 or not body or not cta:
        return _generate_deterministic(analysis, voice_style)

    while len(subject_lines) < 3:
        subject_lines.append(f"From this week's video: {analysis.hook[:60]}")

    return NewsletterContent(
        subject_lines=subject_lines[:5],
        preview_text=preview_text or analysis.hook[:180],
        body=body,
        cta=cta,
    )


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
Write an email newsletter for this creator. Return JSON exactly like this:
{{
  "subject_lines": ["subject 1", "subject 2", "subject 3"],
  "preview_text": "preview line under 180 chars that teases without spoiling",
  "body": "full newsletter body as prose, paragraphs separated by \\n\\n",
  "cta": "closing call to action under 220 chars"
}}

Write in first person. Three subject line options, all specific to this video.\
"""


# ---------------------------------------------------------------------------
# Deterministic fallback — used when no LLM provider is configured (tests)
# ---------------------------------------------------------------------------


def _generate_deterministic(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
) -> NewsletterContent:
    first_idea = analysis.key_ideas[0]
    subject_seed = first_idea.title[:42].rstrip()
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
    if "contrarian" in tone:
        return f"Let me be direct: {hook}"
    if "practical" in tone or "instructional" in tone:
        return f"Here's something practical worth knowing: {hook}"
    if "reflective" in tone or "narrative" in tone:
        return f"Something I keep coming back to: {hook}"
    return hook
