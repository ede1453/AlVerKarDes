from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_shopping_pipeline_vertical_slice_with_profile_store_and_notification():
    client.post("/api/v1/user-profiles/clear")
    client.post(
        "/api/v1/user-profiles/preferences",
        json={
            "user_id": "user-1",
            "preferred_marketplaces": ["saturn"],
            "preferred_brands": ["Apple"],
            "risk_tolerance": "LOW",
        },
    )

    profile = client.get("/api/v1/user-profiles/user-1/recommendation-context")
    assert profile.status_code == 200

    response = client.post(
        "/api/v1/shopping-pipeline/run",
        json={
            "user_id": "user-1",
            "query": "MacBook Air M3 13 inch 512GB",
            "profile_context": profile.json(),
            "claimed_original_price": "1099.00",
            "deliver_notification": True,
            "channels": ["in_app"],
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "COMPLETED"
    assert data["smart_alert"] is not None
    assert data["explanation"] is not None
    assert data["notification"] is not None
