from fastapi.testclient import TestClient

from app.main import app


def test_process_video_creates_completed_job_with_transcript_override() -> None:
    client = TestClient(app)

    process_response = client.post(
        "/api/videos/process",
        json={
            "youtube_url": "https://www.youtube.com/watch?v=abc123XYZ_9",
            "platforms": ["twitter", "linkedin"],
            "transcript_text": (
                "A strong creator workflow starts with one specific idea. "
                "The video builds tension around wasted editing time and then shows a payoff. "
                "In 14 days, the creator shipped 8 posts from 2 videos."
            ),
        },
    )

    assert process_response.status_code == 202
    payload = process_response.json()
    assert payload["status"] == "queued"

    job_response = client.get(payload["poll_url"])

    assert job_response.status_code == 200
    job = job_response.json()
    assert job["status"] == "completed"
    assert job["progress"] == 100
    assert len(job["content"]["twitter"]["standalone_tweets"]) == 5
    assert len(job["content"]["linkedin"]["posts"]) == 2
    assert len(job["content"]["newsletter"]["subject_lines"]) == 3
    assert len(job["content"]["blog"]["sections"]) >= 3
    assert len(job["content"]["shorts"]["clips"]) >= 3
    assert len(job["content"]["carousel"]["slides"]) >= 6


def test_get_video_job_returns_404_for_unknown_job() -> None:
    client = TestClient(app)

    response = client.get("/api/videos/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
