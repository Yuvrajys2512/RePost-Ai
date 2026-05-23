from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.voice import VoiceStyle
from app.services.voice import extract_voice_style
from app.agents.nodes.generators.twitter import generate_twitter
from app.agents.nodes.generators.linkedin import generate_linkedin
from app.agents.nodes.generators.newsletter import generate_newsletter
from app.agents.nodes.generators.blog import generate_blog
from app.agents.nodes.generators.shorts import generate_shorts
from app.agents.nodes.generators.carousel import generate_carousel
from app.agents.nodes.analyzer import analyze_content
from app.services.transcript import transcript_from_text


SAMPLES = [
    "Stop summarizing your videos. Use a framework that keeps the hook and payoff.",
    "Here's how creators turn one story into many practical posts.",
]

CONTRARIAN_SAMPLES = [
    "Most content advice is wrong. Stop chasing formats that don't fit your story.",
    "The mistake every creator makes is treating a video like a blog post.",
]


def _make_analysis():
    transcript = transcript_from_text(
        "This is a test transcript about content repurposing strategies "
        "for creators who want to grow their audience in 2024. "
        "The mistake most people make is treating every platform the same. "
        "Here is a step by step framework to fix that.",
        video_id="test123",
    )
    return analyze_content(transcript)


# --- Voice extraction ---

def test_extract_voice_style_returns_contract() -> None:
    style = extract_voice_style(SAMPLES)
    assert style.sample_count == 2
    assert style.tone in {
        "direct and contrarian",
        "practical and instructional",
        "reflective and narrative",
        "clear and pragmatic",
    }
    assert isinstance(style.vocabulary, list)
    assert style.sentence_length in {"short and punchy", "balanced", "long-form and explanatory"}
    assert style.emoji_usage in {"frequent", "minimal"}


def test_contrarian_tone_detected() -> None:
    style = extract_voice_style(CONTRARIAN_SAMPLES)
    assert style.tone == "direct and contrarian"


def test_instructional_tone_detected() -> None:
    instructional_samples = ["Here's how to build a step-by-step framework for content systems."]
    style = extract_voice_style(instructional_samples)
    assert style.tone == "practical and instructional"


# --- Voice-injected generator tests ---

def test_generators_accept_voice_style_without_error() -> None:
    """All generators should run cleanly with a VoiceStyle injected."""
    analysis = _make_analysis()
    voice = extract_voice_style(SAMPLES)

    twitter = generate_twitter(analysis, voice)
    assert len(twitter.standalone_tweets) == 5
    assert len(twitter.thread) >= 5

    linkedin = generate_linkedin(analysis, voice)
    assert len(linkedin.posts) == 2

    newsletter = generate_newsletter(analysis, voice)
    assert len(newsletter.subject_lines) == 3

    blog = generate_blog(analysis, voice)
    assert len(blog.sections) >= 3

    shorts = generate_shorts(analysis, voice)
    assert len(shorts.clips) >= 3

    carousel = generate_carousel(analysis, voice)
    assert len(carousel.slides) >= 6


def test_generators_work_without_voice_style() -> None:
    """All generators should still work when voice_style is None (backward-compatible)."""
    analysis = _make_analysis()

    assert generate_twitter(analysis, None).standalone_tweets
    assert generate_linkedin(analysis, None).posts
    assert generate_newsletter(analysis, None).body
    assert generate_blog(analysis, None).sections
    assert generate_shorts(analysis, None).clips
    assert generate_carousel(analysis, None).slides


def test_voice_tone_appears_in_twitter_thread_hook() -> None:
    """Contrarian tone should inject 'Unpopular take' prefix into Twitter thread hook."""
    analysis = _make_analysis()
    contrarian_voice = extract_voice_style(CONTRARIAN_SAMPLES)
    twitter = generate_twitter(analysis, contrarian_voice)
    assert "Unpopular take" in twitter.thread[0].text


# --- API endpoint tests ---

def test_create_voice_profile_endpoint() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/voice-profile",
        json={
            "name": "Creator voice",
            "samples": [
                "Here's how I think about content systems. Start with the story, then adapt it.",
            ],
        },
        headers={"Authorization": "Bearer mock-user-token"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Creator voice"
    assert payload["extracted_style"]["sample_count"] == 1
    assert "id" in payload
    assert "created_at" in payload


def test_list_voice_profiles_endpoint() -> None:
    client = TestClient(app)

    # Create a profile first
    client.post(
        "/api/voice-profile",
        json={"name": "Profile A", "samples": ["Stop doing this wrong. Here's the fix."]},
        headers={"Authorization": "Bearer mock-user-token"},
    )

    response = client.get(
        "/api/voice-profile",
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "profiles" in data
    assert "total" in data
    assert data["total"] >= 1


def test_get_voice_profile_by_id() -> None:
    client = TestClient(app)

    # Create
    create_resp = client.post(
        "/api/voice-profile",
        json={"name": "My Voice", "samples": ["Framework-driven. Step by step."]},
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert create_resp.status_code == 201
    profile_id = create_resp.json()["id"]

    # Fetch by ID
    get_resp = client.get(
        f"/api/voice-profile/{profile_id}",
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == profile_id


def test_delete_voice_profile_endpoint() -> None:
    client = TestClient(app)

    # Create
    create_resp = client.post(
        "/api/voice-profile",
        json={"name": "To Delete", "samples": ["I learned this the hard way. Here's the story."]},
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert create_resp.status_code == 201
    profile_id = create_resp.json()["id"]

    # Delete
    del_resp = client.delete(
        f"/api/voice-profile/{profile_id}",
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert del_resp.status_code == 204

    # Confirm gone
    get_resp = client.get(
        f"/api/voice-profile/{profile_id}",
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert get_resp.status_code == 404
