from __future__ import annotations

from app.agents.llm import call_llm_json, has_llm_provider
from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import LinkedInContent, LinkedInPost
from app.schemas.voice import VoiceStyle

_SYSTEM_PROMPT = """\
You are a world-class LinkedIn ghostwriter for YouTube creators.

You take a content analysis of a YouTube video and write LinkedIn posts that the
CREATOR THEMSELVES would publish — in their voice, as their own content.

RULES — read every one:
- Write AS the creator. First person: "I", "my", "we". Always.
- Never write "The creator" or "They argue". You are writing what THEY would post.
- Treat the video's insights as your own lived experience and perspective.

LinkedIn post format (non-negotiable):
  Line 1 — HOOK: One punchy sentence. Creates a curiosity gap or makes a bold claim.
            This determines if anyone reads on. Make it arresting.
  [blank line]
  BODY: 150-300 words across multiple short paragraphs (2-3 sentences max each).
    - Open with the specific situation or problem you faced
    - Share the key insight with specificity — use actual numbers, quotes, or moments from the video
    - Build to the practical implication — what this means for the reader
    - White space is your friend. Short paragraphs. One idea per paragraph.
  [blank line]
  CTA: A specific question that comes directly from this content. Not "What do you think?"
       Something only someone who watched/read this could meaningfully answer.

Write TWO posts that approach the content from completely different angles:
  Post 1: Lead with the most provocative or counterintuitive idea
  Post 2: Lead with a personal story angle or the practical how-to angle

If a voice profile is provided, match the creator's tone, sentence rhythm, and vocabulary.\
"""


def generate_linkedin(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
) -> LinkedInContent:
    if has_llm_provider():
        try:
            return _generate_with_llm(analysis, voice_style)
        except Exception:
            pass
    return _generate_deterministic(analysis, voice_style)


def _generate_with_llm(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None,
) -> LinkedInContent:
    user_message = _build_user_message(analysis, voice_style)
    data = call_llm_json(_SYSTEM_PROMPT, user_message, temperature=0.65)

    posts: list[LinkedInPost] = []
    for raw in data.get("posts", []):
        hook = raw.get("hook", "")[:220].strip()
        body = raw.get("body", "").strip()
        cta = raw.get("cta", "")[:220].strip()

        if not hook or not body or not cta:
            continue
        if len(body.split()) < 25:
            continue

        posts.append(LinkedInPost(hook=hook, body=body, cta=cta))

    if len(posts) < 2:
        return _generate_deterministic(analysis, voice_style)

    return LinkedInContent(posts=posts[:3])


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
Write two LinkedIn posts for this creator. Return JSON exactly like this:
{{
  "posts": [
    {{
      "hook": "single hook line under 220 chars",
      "body": "full body text with paragraph breaks using \\n\\n",
      "cta": "specific closing question under 220 chars"
    }},
    {{
      "hook": "different angle hook line",
      "body": "full body text with paragraph breaks using \\n\\n",
      "cta": "different specific closing question"
    }}
  ]
}}

Write in first person. No "The creator". Two completely different angles.\
"""


# ---------------------------------------------------------------------------
# Deterministic fallback — used when no LLM provider is configured (tests)
# ---------------------------------------------------------------------------


def _generate_deterministic(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
) -> LinkedInContent:
    first_idea = analysis.key_ideas[0]
    second_idea = analysis.key_ideas[min(1, len(analysis.key_ideas) - 1)]
    data_note = f" {analysis.data_points[0]}" if analysis.data_points else ""
    takeaway = analysis.audience_takeaway.rstrip(".")

    posts = [
        LinkedInPost(
            hook=analysis.hook[:220],
            body=(
                f"{first_idea.summary}{data_note}\n\n"
                f"The shift happens when you stop treating this as a background habit "
                f"and start seeing it as an active choice.\n\n"
                f"{takeaway}."
            ),
            cta=_voice_cta("How are you approaching this in your own workflow?", voice_style),
        ),
        LinkedInPost(
            hook=f"Most people overlook this: {first_idea.title}"[:220],
            body=(
                f"{second_idea.summary}\n\n"
                f"I tested this myself. The results surprised me.\n\n"
                f"{takeaway}."
            ),
            cta=_voice_cta("What's your take — has this come up for you?", voice_style),
        ),
    ]
    return LinkedInContent(posts=posts)


def _voice_cta(default: str, voice_style: VoiceStyle | None) -> str:
    if voice_style is None:
        return default
    tone = voice_style.tone
    if "contrarian" in tone:
        return "Disagree? Tell me why below."
    if "practical" in tone or "instructional" in tone:
        return "Try this with your next video and share what happens."
    if "reflective" in tone or "narrative" in tone:
        return "What moment shifted how you think about this?"
    return default
