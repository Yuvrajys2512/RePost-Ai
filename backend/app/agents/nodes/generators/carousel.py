from __future__ import annotations

from app.agents.llm import call_llm_json, has_llm_provider
from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import CarouselContent, CarouselSlide
from app.schemas.voice import VoiceStyle

_SYSTEM_PROMPT = """\
You are a world-class Instagram/LinkedIn carousel ghostwriter for YouTube creators.

You take a content analysis of a YouTube video and write a carousel post that the
CREATOR THEMSELVES would publish — in their voice, as their own content.

RULES:
- Write AS the creator. First person: "I", "my", "we". Always.
- Carousels are scroll-stopping, educational, and visually structured.
- Slide 1 (cover): One bold headline — the single most compelling promise of the carousel.
  Should make someone swipe. Under 90 characters.
- Slides 2-8 (value slides): Each slide = one idea. Tight.
  Headline: the insight in one line (under 90 chars).
  Body: 1-3 sentences explaining or proving the insight (under 220 chars).
  No bullet points within slides — each slide IS the bullet.
- Last slide (CTA): Ask a question or invite action. Headline = the ask. Body = why it matters.
- Write 6-9 total slides (cover + value slides + CTA = 6 minimum).
- Caption: 1-2 sentences. What this carousel teaches + a soft hook to swipe.
  Use specific language from the video, not generic "check this out".
- If a voice profile is provided, match the creator's tone and vocabulary.\
"""


def generate_carousel(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
) -> CarouselContent:
    if has_llm_provider():
        try:
            return _generate_with_llm(analysis, voice_style)
        except Exception:
            pass
    return _generate_deterministic(analysis, voice_style)


def _generate_with_llm(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None,
) -> CarouselContent:
    user_message = _build_user_message(analysis, voice_style)
    data = call_llm_json(_SYSTEM_PROMPT, user_message, temperature=0.65)

    title = (data.get("title") or "").strip()[:100]
    caption = (data.get("caption") or "").strip()
    raw_slides = data.get("slides", [])

    slides: list[CarouselSlide] = []
    for i, s in enumerate(raw_slides[:10], start=1):
        headline = (s.get("headline") or "").strip()[:90]
        body = (s.get("body") or "").strip()[:220]
        if not headline or not body:
            continue
        slides.append(CarouselSlide(slide_number=i, headline=headline, body=body))

    if not title or len(slides) < 6:
        return _generate_deterministic(analysis, voice_style)

    return CarouselContent(
        title=title,
        slides=slides[:10],
        caption=caption or f"{analysis.hook[:100]} Save this.",
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
{voice_section}
Write a carousel post for this creator. Return JSON exactly like this:
{{
  "title": "cover slide headline under 100 chars",
  "slides": [
    {{"headline": "slide headline under 90 chars", "body": "1-3 sentences under 220 chars"}},
    {{"headline": "slide headline", "body": "slide body"}},
    {{"headline": "slide headline", "body": "slide body"}},
    {{"headline": "slide headline", "body": "slide body"}},
    {{"headline": "slide headline", "body": "slide body"}},
    {{"headline": "CTA question or action", "body": "why this matters or what to do"}}
  ],
  "caption": "1-2 sentence caption specific to this video"
}}

6-9 slides total (cover through CTA). First person. Use specific details from this video.\
"""


# ---------------------------------------------------------------------------
# Deterministic fallback — used when no LLM provider is configured (tests)
# ---------------------------------------------------------------------------


def _generate_deterministic(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
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
    if "contrarian" in tone:
        return f"The honest version: {takeaway}"
    if "practical" in tone or "instructional" in tone:
        return f"Action step: {takeaway}"
    if "reflective" in tone or "narrative" in tone:
        return f"The lesson I keep sharing: {takeaway}"
    return takeaway
