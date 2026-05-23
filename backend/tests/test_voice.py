from fastapi.testclient import TestClient

from app.main import app
from app.services.voice import extract_voice_style


def test_extract_voice_style_returns_contract() -> None:
    style = extract_voice_style(
        [
            "Stop summarizing your videos. Use a framework that keeps the hook and payoff.",
            "Here's how creators turn one story into many practical posts.",
        ]
    )

    assert style.sample_count == 2
    assert style.tone in {
        "direct and contrarian",
        "practical and instructional",
        "reflective and narrative",
        "clear and pragmatic",
    }


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
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Creator voice"
    assert payload["extracted_style"]["sample_count"] == 1
