from __future__ import annotations

from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import TwitterContent, TwitterTweet
from app.schemas.voice import VoiceStyle


def generate_twitter(
    analysis: ContentAnalysis, voice_style: VoiceStyle | None = None
) -> TwitterContent:
    # Apply voice tone to the opener if a voice profile is available
    opener = _voice_opener(analysis.hook, voice_style)

    standalone = [
        TwitterTweet(text=_fit_tweet(f"{idea.title}: {idea.summary}"))
        for idea in analysis.key_ideas
    ]
    while len(standalone) < 5:
        standalone.append(
            TwitterTweet(text=_fit_tweet(f"{opener} The takeaway: {analysis.audience_takeaway}"))
        )

    thread = [
        TwitterTweet(text=_fit_tweet(opener)),
        *[
            TwitterTweet(text=_fit_tweet(f"{index}. {idea.summary}"))
            for index, idea in enumerate(analysis.key_ideas[:4], start=1)
        ],
        TwitterTweet(text=_fit_tweet(f"Bottom line: {analysis.audience_takeaway}")),
    ]
    while len(thread) < 5:
        thread.insert(-1, TwitterTweet(text=_fit_tweet(analysis.summary)))

    return TwitterContent(standalone_tweets=standalone[:5], thread=thread[:6])


def _voice_opener(hook: str, voice_style: VoiceStyle | None) -> str:
    if voice_style is None:
        return hook
    tone = voice_style.tone
    if tone == "direct and contrarian":
        return f"Unpopular take: {hook}"
    if tone == "practical and instructional":
        return f"Here's how to think about this: {hook}"
    if tone == "reflective and narrative":
        return f"This changed how I look at it: {hook}"
    return hook


def _fit_tweet(text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) <= 280:
        return clean
    return clean[:276].rstrip() + "..."
