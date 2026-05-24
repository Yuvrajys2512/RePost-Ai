from __future__ import annotations

from app.agents.llm import call_llm_json, has_llm_provider
from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import TwitterContent, TwitterTweet
from app.schemas.voice import VoiceStyle

_SYSTEM_PROMPT = """\
You are a world-class Twitter/X ghostwriter for YouTube creators.

You take a content analysis of a YouTube video and write Twitter content that the
CREATOR THEMSELVES would publish — in their voice, as their own posts.

RULES — read every one:
- Write AS the creator, not about them. Never write "The creator says" or "They argue".
  Use first person where it sounds natural: "I stopped doing X", "Here's what I found".
- Every tweet must be specific to THIS video. A tweet that could apply to any video is a failure.
- Standalone tweets: 5 COMPLETELY DIFFERENT tweets, each from a different angle.
  No two tweets can make the same point. Do NOT repeat the hook.
- Thread rules:
    Tweet 1 (hook): The most provocative or surprising claim. Makes someone stop scrolling.
    Tweets 2-5 (value): Each one is a tight, punchy standalone thought that builds on the last.
      Write them as natural sentences — NO numbering like "1." "2/" "3.". They flow, not list.
    Tweet 6 (CTA): Simple. What to do next. Link back to the video or invite a reply.
- Every single tweet must be under 280 characters. Count carefully.
- No "🧵 Thread:" announcements. No "/end". No "fin".
- Use the exact quotes and specific data points from the analysis — they are your raw material.
- If a voice profile is provided, match the creator's tone, sentence length, and style.\
"""


def generate_twitter(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
) -> TwitterContent:
    if has_llm_provider():
        try:
            return _generate_with_llm(analysis, voice_style)
        except Exception:
            pass
    return _generate_deterministic(analysis, voice_style)


def _generate_with_llm(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None,
) -> TwitterContent:
    user_message = _build_user_message(analysis, voice_style)
    data = call_llm_json(_SYSTEM_PROMPT, user_message, temperature=0.7)

    standalone = [
        TwitterTweet(text=_fit(t))
        for t in data.get("standalone_tweets", [])
        if t.strip()
    ]
    thread = [
        TwitterTweet(text=_fit(t))
        for t in data.get("thread", [])
        if t.strip()
    ]

    # Pad to schema minimums if the model returned fewer than required
    while len(standalone) < 5:
        standalone.append(TwitterTweet(text=_fit(analysis.hook)))
    while len(thread) < 5:
        thread.append(TwitterTweet(text=_fit(analysis.audience_takeaway)))

    return TwitterContent(standalone_tweets=standalone[:8], thread=thread[:8])


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
Write Twitter content for this creator. Return JSON exactly like this:
{{
  "standalone_tweets": ["tweet1", "tweet2", "tweet3", "tweet4", "tweet5"],
  "thread": ["hook tweet", "value tweet", "value tweet", "value tweet", "value tweet", "cta tweet"]
}}

All tweets must be under 280 characters. No numbered lists. No "The creator says".\
"""


def _fit(text: str) -> str:
    clean = " ".join(text.split())
    return clean[:277].rstrip() + "..." if len(clean) > 280 else clean


# ---------------------------------------------------------------------------
# Deterministic fallback — used when no LLM provider is configured (tests)
# ---------------------------------------------------------------------------


def _generate_deterministic(
    analysis: ContentAnalysis,
    voice_style: VoiceStyle | None = None,
) -> TwitterContent:
    opener = _voice_opener(analysis.hook, voice_style)

    seen: set[str] = set()
    standalone: list[TwitterTweet] = []
    for idea in analysis.key_ideas:
        text = _fit(f"{idea.title}: {idea.summary}")
        if text not in seen:
            seen.add(text)
            standalone.append(TwitterTweet(text=text))
    while len(standalone) < 5:
        fallback = _fit(f"{opener} — {analysis.audience_takeaway}")
        standalone.append(TwitterTweet(text=fallback))

    thread = [
        TwitterTweet(text=_fit(opener)),
        *[
            TwitterTweet(text=_fit(idea.summary))
            for idea in analysis.key_ideas[:4]
        ],
        TwitterTweet(text=_fit(analysis.audience_takeaway)),
    ]
    while len(thread) < 5:
        thread.insert(-1, TwitterTweet(text=_fit(analysis.summary)))

    return TwitterContent(standalone_tweets=standalone[:5], thread=thread[:6])


def _voice_opener(hook: str, voice_style: VoiceStyle | None) -> str:
    if voice_style is None:
        return hook
    tone = voice_style.tone
    if "contrarian" in tone:
        return f"Unpopular take: {hook}"
    if "practical" in tone or "instructional" in tone:
        return f"Here's how to think about this: {hook}"
    if "reflective" in tone or "narrative" in tone:
        return f"This changed how I see it: {hook}"
    return hook
