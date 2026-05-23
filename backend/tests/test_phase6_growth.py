from fastapi.testclient import TestClient

from app.main import app


def test_phase6_growth_features() -> None:
    client = TestClient(app)

    # 1. Verify API Key endpoint is gated (free plan cannot provision keys)
    client.post(
        "/api/billing/mock-charge",
        json={"plan": "free"},
        headers={"Authorization": "Bearer mock-user-token"},
    )
    unauth_key_res = client.post(
        "/api/billing/keys",
        json={"name": "Test Token"},
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert unauth_key_res.status_code == 403

    # 2. Upgrade to Agency Plan to generate keys
    charge_res = client.post(
        "/api/billing/mock-charge",
        json={"plan": "agency"},
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert charge_res.status_code == 200
    assert charge_res.json()["user"]["plan"] == "agency"

    # 3. Create a Developer API Key
    create_key_res = client.post(
        "/api/billing/keys",
        json={"name": "Production Key"},
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert create_key_res.status_code == 200
    key_data = create_key_res.json()["key"]
    assert key_data["name"] == "Production Key"
    assert key_data["key_value"].startswith("rp_live_")
    api_key_value = key_data["key_value"]
    api_key_id = key_data["id"]

    # 4. Fetch list of API keys
    list_keys_res = client.get(
        "/api/billing/keys",
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert list_keys_res.status_code == 200
    keys_list = list_keys_res.json()
    assert len(keys_list) >= 1
    assert any(k["id"] == api_key_id for k in keys_list)

    # 5. Programmatic Video Processing using X-API-Key header
    prog_res = client.post(
        "/api/videos/process",
        json={
            "youtube_url": "https://www.youtube.com/watch?v=growth12345",
            "platforms": ["twitter", "linkedin"],
            "transcript_text": "This is a growth transcript about creator marketing and API scaling.",
        },
        headers={"X-API-Key": api_key_value},
    )
    assert prog_res.status_code == 202
    job_data = prog_res.json()
    job_id = job_data["job_id"]

    # 6. Verify API access is restricted if plan is downgraded from Agency
    client.post(
        "/api/billing/mock-charge",
        json={"plan": "starter"},
        headers={"Authorization": "Bearer mock-user-token"},
    )
    demoted_res = client.post(
        "/api/videos/process",
        json={
            "youtube_url": "https://www.youtube.com/watch?v=growth12345",
            "platforms": ["twitter"],
        },
        headers={"X-API-Key": api_key_value},
    )
    assert demoted_res.status_code == 403  # Restricted to Agency tier

    # Upgrade back to agency to complete tests
    client.post(
        "/api/billing/mock-charge",
        json={"plan": "agency"},
        headers={"Authorization": "Bearer mock-user-token"},
    )

    # 7. Query database to get a generated content piece ID for testing Variations & Analytics
    import asyncio
    async def get_content_info():
        from app.db.session import AsyncSessionLocal
        from app.models.video import GeneratedContentModel
        from sqlalchemy import select
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GeneratedContentModel).where(GeneratedContentModel.video_job_id == str(job_id))
            )
            item = result.scalars().first()
            return (item.id, item.platform) if item else (None, None)

    content_id, content_platform = asyncio.run(get_content_info())
    assert content_id is not None
    assert content_platform is not None


    # 8. Test A/B Variations Generator for content piece
    vars_res = client.post(
        f"/api/content/{content_id}/variations",
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert vars_res.status_code == 200
    vars_payload = vars_res.json()
    assert "variations" in vars_payload
    assert len(vars_payload["variations"]) == 3

    # 9. Test Analytics Tracking Event
    track_res = client.post(
        f"/api/content/{content_id}/track",
        json={"action": "content_copied", "platform": content_platform},
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert track_res.status_code == 200
    assert track_res.json()["status"] == "success"

    # 10. Test Analytics dashboard endpoint
    analytics_res = client.get(
        "/api/analytics",
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["total_runs"] >= 1
    assert content_platform.lower() in analytics_data["platform_distribution"]
    assert analytics_data["platform_distribution"][content_platform.lower()] >= 1
    assert len(analytics_data["recent_activity"]) >= 1
    assert analytics_data["recent_activity"][0]["action"] == "content_copied"

    # 11. Revoke the API Key
    revoke_res = client.delete(
        f"/api/billing/keys/{api_key_id}",
        headers={"Authorization": "Bearer mock-user-token"},
    )
    assert revoke_res.status_code == 200

    # 12. Try to use revoked key, must return 401
    revoked_key_res = client.post(
        "/api/videos/process",
        json={
            "youtube_url": "https://www.youtube.com/watch?v=growth12345",
            "platforms": ["twitter"],
        },
        headers={"X-API-Key": api_key_value},
    )
    assert revoked_key_res.status_code == 401
