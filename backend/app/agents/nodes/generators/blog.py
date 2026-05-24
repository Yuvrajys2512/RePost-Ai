from __future__ import annotations

from app.agents.llm import call_llm_json, has_llm_provider
from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import BlogContent, BlogSection
from app.schemas.voice import VoiceStyle

_SYSTEM_PROMPT = """\
You are a world-class blog ghostwriter for YouTube creators.

You take a content analysis of a YouTube video and write a long-form blog post that the
CREATOR THEMSELVES would publish — in their voice, as their own article.

RULES:
- Write AS the creator. First person: "I", "my", "we". Always.
- Never write "The creator says" or "They argue". You are writing what THEY would publish.
- This is a blog post, not a transcript summary. Reframe the video's ideas as readable prose.
- Title: specific and compelling. Should make someone click from search or social.
  Under 120 characters. No clickbait — accurate and intriguing.
- Meta description: 1-2 sentences, what the post delivers, under 160 characters. No fluff.
- Introduction: 2-3 short paragraphs. Open with the hook, establish the problem or question,
  tell the reader what they'll get from reading. No "In this post I will..."
- Sections: 3-5 sections, each with a sharp heading and 100-200 words of prose.
  Each section should be a distinct insight, not just a rephrased bullet point.
  Use specific examples, numbers, and quotes from the analysis.
- Conclusion: 2-3 sentences. The lasting thought. What the reader should do or think differently.
- If a voice profile is provided, match the creator's tone, sentence rhythm, and vocabulary.\
"""


def generate_blog(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
) -> BlogContent:
    if has_llm_provider():
        try:
            return _generate_with_llm(analysis, voice_style)
        except Exception:
            pass
    return _generate_deterministic(analysis, voice_style)


def _generate_with_llm(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None,
) -> BlogContent:
    user_message = _build_user_message(analysis, voice_style)
    data = call_llm_json(_SYSTEM_PROMPT, user_message, temperature=0.65)

    title = (data.get("title") or "").strip()[:120]
    meta = (data.get("meta_description") or "").strip()[:160]
    intro = (data.get("introduction") or "").strip()
    conclusion = (data.get("conclusion") or "").strip()

    raw_sections = data.get("sections", [])
    sections = [
        BlogSection(
            heading=(s.get("heading") or "")[:140].strip(),
            body=(s.get("body") or "").strip(),
        )
        for s in raw_sections
        if (s.get("heading") or "").strip() and (s.get("body") or "").strip()
    ]

    if not title or not intro or len(sections) < 3:
        return _generate_deterministic(analysis, voice_style)

    while len(sections) < 3:
        sections.append(
            BlogSection(
                heading="What this means for you",
                body=analysis.audience_takeaway,
            )
        )

    return BlogContent(
        title=title,
        meta_description=meta or analysis.summary[:160],
        introduction=intro,
        sections=sections[:5],
        conclusion=conclusion or f"Bottom line: {analysis.audience_takeaway}",
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
    story_beats = "\n".join(
        f"  - {beat.label}: {beat.description}" for beat in analysis.story_structure
    )

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

Story structure:
{story_beats}
{voice_section}
Write a blog post for this creator. Return JSON exactly like this:
{{
  "title": "post title under 120 chars",
  "meta_description": "1-2 sentences under 160 chars",
  "introduction": "2-3 paragraphs separated by \\n\\n",
  "sections": [
    {{"heading": "section heading under 140 chars", "body": "section prose 100-200 words"}},
    {{"heading": "section heading", "body": "section prose"}},
    {{"heading": "section heading", "body": "section prose"}}
  ],
  "conclusion": "2-3 sentences"
}}

Write in first person. 3-5 sections. Use specific quotes and data from the analysis.\
"""


# ---------------------------------------------------------------------------
# Deterministic fallback — used when no LLM provider is configured (tests)
# ---------------------------------------------------------------------------


def _generate_deterministic(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
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
    if "contrarian" in tone:
        return "Most people get this wrong. "
    if "practical" in tone or "instructional" in tone:
        return "Here's a framework worth understanding. "
    if "reflective" in tone or "narrative" in tone:
        return "This took me a while to figure out. "
    return ""
