from app.schemas.analysis import ContentAnalysis
from app.schemas.generation import TwitterContent, TwitterTweet


def generate_twitter(analysis: ContentAnalysis) -> TwitterContent:
    standalone = [
        TwitterTweet(text=_fit_tweet(f"{idea.title}: {idea.summary}"))
        for idea in analysis.key_ideas
    ]
    while len(standalone) < 5:
        standalone.append(
            TwitterTweet(text=_fit_tweet(f"{analysis.hook} The takeaway: {analysis.audience_takeaway}"))
        )

    thread = [
        TwitterTweet(text=_fit_tweet(analysis.hook)),
        *[
            TwitterTweet(text=_fit_tweet(f"{index}. {idea.summary}"))
            for index, idea in enumerate(analysis.key_ideas[:4], start=1)
        ],
        TwitterTweet(text=_fit_tweet(f"Bottom line: {analysis.audience_takeaway}")),
    ]
    while len(thread) < 5:
        thread.insert(-1, TwitterTweet(text=_fit_tweet(analysis.summary)))

    return TwitterContent(standalone_tweets=standalone[:5], thread=thread[:6])


def _fit_tweet(text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) <= 280:
        return clean
    return clean[:276].rstrip() + "..."

