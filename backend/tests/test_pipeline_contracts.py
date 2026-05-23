import pytest

from app.agents.graph import run_pipeline_for_transcript
from app.agents.nodes.analyzer import analyze_content
from app.agents.nodes.generators.blog import generate_blog
from app.agents.nodes.generators.carousel import generate_carousel
from app.agents.nodes.generators.linkedin import generate_linkedin
from app.agents.nodes.generators.newsletter import generate_newsletter
from app.agents.nodes.generators.shorts import generate_shorts
from app.agents.nodes.generators.twitter import generate_twitter
from app.schemas.transcript import Transcript, TranscriptSegment
from app.services.transcript import extract_youtube_video_id, transcript_from_text


SAMPLE_TRANSCRIPT = (
    "Most creators think repurposing means summarizing a video, but that is the wrong goal. "
    "The real goal is to preserve the story structure: hook, tension, insight, and payoff. "
    "In 30 days, one creator turned a single weekly video into 12 platform-native posts. "
    "The surprising lesson was that specificity outperformed volume every time. "
    "They learned to pull one sharp idea from each section instead of flattening the entire video."
)


@pytest.mark.parametrize(
    ("url", "video_id"),
    [
        ("https://www.youtube.com/watch?v=abc123XYZ_9", "abc123XYZ_9"),
        ("https://youtu.be/abc123XYZ_9", "abc123XYZ_9"),
        ("https://www.youtube.com/shorts/abc123XYZ_9", "abc123XYZ_9"),
        ("https://www.youtube.com/embed/abc123XYZ_9", "abc123XYZ_9"),
    ],
)
def test_extract_youtube_video_id(url: str, video_id: str) -> None:
    assert extract_youtube_video_id(url) == video_id


def test_extract_youtube_video_id_rejects_non_youtube_url() -> None:
    with pytest.raises(ValueError):
        extract_youtube_video_id("https://example.com/watch?v=abc123")


def test_transcript_from_text_creates_contract() -> None:
    transcript = transcript_from_text(SAMPLE_TRANSCRIPT, video_id="sample-video")

    assert transcript.video_id == "sample-video"
    assert transcript.text.startswith("Most creators think")
    assert transcript.duration_seconds > 0


def test_analyze_content_returns_schema() -> None:
    transcript = transcript_from_text(SAMPLE_TRANSCRIPT, video_id="sample-video")

    analysis = analyze_content(transcript)

    assert analysis.video_id == "sample-video"
    assert analysis.hook
    assert len(analysis.key_ideas) >= 1
    assert analysis.data_points == [
        "In 30 days, one creator turned a single weekly video into 12 platform-native posts."
    ]


def test_generators_return_valid_platform_contracts() -> None:
    analysis = analyze_content(transcript_from_text(SAMPLE_TRANSCRIPT))

    twitter = generate_twitter(analysis)
    linkedin = generate_linkedin(analysis)
    newsletter = generate_newsletter(analysis)
    blog = generate_blog(analysis)
    shorts = generate_shorts(analysis)
    carousel = generate_carousel(analysis)

    assert len(twitter.standalone_tweets) == 5
    assert len(twitter.thread) >= 5
    assert all(len(tweet.text) <= 280 for tweet in twitter.standalone_tweets + twitter.thread)
    assert len(linkedin.posts) == 2
    assert all(post.text.count("\n\n") == 2 for post in linkedin.posts)
    assert len(newsletter.subject_lines) == 3
    assert len(blog.sections) >= 3
    assert len(shorts.clips) >= 3
    assert len(carousel.slides) >= 6


def test_pipeline_runs_end_to_end_from_transcript() -> None:
    transcript = Transcript(
        video_id="sample-video",
        source_url="manual://test",
        segments=[
            TranscriptSegment(start_seconds=0, duration_seconds=30, text=SAMPLE_TRANSCRIPT),
        ],
    )

    result = run_pipeline_for_transcript(transcript)

    assert result.transcript.video_id == "sample-video"
    assert result.analysis.key_ideas
    assert result.content.twitter.thread
    assert result.content.linkedin.posts
    assert result.content.newsletter.body
    assert result.content.blog.sections
    assert result.content.shorts.clips
    assert result.content.carousel.slides
