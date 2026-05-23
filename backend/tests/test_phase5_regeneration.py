from fastapi.testclient import TestClient

from app.main import app


def test_platform_content_regeneration() -> None:
    client = TestClient(app)

    # 1. Reset user plan and quota
    client.post(
        "/api/billing/mock-charge",
        json={"plan": "free"},
        headers={"Authorization": "Bearer mock-user-token"},
    )

    # 2. Process a video job
    process_response = client.post(
        "/api/videos/process",
        json={
            "youtube_url": "https://www.youtube.com/watch?v=abc123XYZ_9",
            "platforms": ["twitter", "linkedin"],
            "transcript_text": "A strong creator workflow starts with one specific idea. The video builds tension.",
        },
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert process_response.status_code == 202
    job_id = process_response.json()["job_id"]

    # 3. Call the single-platform regeneration endpoint
    regen_response = client.post(
        f"/api/videos/{job_id}/regenerate",
        json={"platform": "linkedin"},
        headers={"Authorization": "Bearer mock-user-token"},
    )

    print("REGEN RESPONSE BODY:", regen_response.json())
    assert regen_response.status_code == 200
    payload = regen_response.json()
    assert payload["status"] == "success"
    assert payload["platform"] == "linkedin"
    assert len(payload["payload"]["posts"]) == 2
    assert payload["payload"]["posts"][0]["hook"] != ""
