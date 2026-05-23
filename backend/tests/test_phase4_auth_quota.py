from fastapi.testclient import TestClient

from app.main import app


def test_quota_limits_and_mock_upgrades() -> None:
    client = TestClient(app)

    # 1. Reset user plan to 'free' and videos_used_this_month = 0 for deterministic testing
    response = client.post(
        "/api/billing/mock-charge",
        json={"plan": "free"},
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["user"]["plan"] == "free"
    assert payload["user"]["videos_used_this_month"] == 0

    # 2. Run first conversion - should succeed (1/2 runs used)
    response = client.post(
        "/api/videos/process",
        json={
            "youtube_url": "https://www.youtube.com/watch?v=abc123XYZ_9",
            "platforms": ["twitter", "linkedin"],
            "transcript_text": "Sample transcript text for run 1.",
        },
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert response.status_code == 202

    # 3. Run second conversion - should succeed (2/2 runs used)
    response = client.post(
        "/api/videos/process",
        json={
            "youtube_url": "https://www.youtube.com/watch?v=abc123XYZ_9",
            "platforms": ["twitter", "linkedin"],
            "transcript_text": "Sample transcript text for run 2.",
        },
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert response.status_code == 202

    # 4. Run third conversion - should exceed quota (3/2 runs -> 403 Forbidden)
    response = client.post(
        "/api/videos/process",
        json={
            "youtube_url": "https://www.youtube.com/watch?v=abc123XYZ_9",
            "platforms": ["twitter", "linkedin"],
            "transcript_text": "Sample transcript text for run 3.",
        },
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert response.status_code == 403
    assert "limit reached" in response.json()["detail"].lower()

    # 5. Simulate subscription upgrade to 'starter' plan (10 runs allowed)
    response = client.post(
        "/api/billing/mock-charge",
        json={"plan": "starter"},
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["plan"] == "starter"

    # 6. Run process again under upgraded tier - should succeed!
    response = client.post(
        "/api/videos/process",
        json={
            "youtube_url": "https://www.youtube.com/watch?v=abc123XYZ_9",
            "platforms": ["twitter", "linkedin"],
            "transcript_text": "Sample transcript text for run 4.",
        },
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert response.status_code == 202
