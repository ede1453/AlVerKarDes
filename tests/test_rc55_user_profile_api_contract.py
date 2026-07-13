from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_user_profile_api_preferences_feedback_and_context():
    client.post("/api/v1/user-profiles/clear")

    preferences = client.post(
        "/api/v1/user-profiles/preferences",
        json={
            "user_id": "user-1",
            "preferred_marketplaces": ["saturn"],
            "preferred_brands": ["Apple"],
            "risk_tolerance": "LOW",
        },
    )
    assert preferences.status_code == 200
    assert preferences.json()["preferred_marketplaces"] == ["saturn"]

    merge = client.post(
        "/api/v1/user-profiles/feedback/merge",
        json={
            "user_id": "user-1",
            "feedback_summary": {
                "event_count": 2,
                "preferred_product_keys": ["macbook-air"],
                "avoided_product_keys": ["iphone"],
            },
        },
    )
    assert merge.status_code == 200
    assert merge.json()["preferred_product_keys"] == ["macbook-air"]

    context = client.get("/api/v1/user-profiles/user-1/recommendation-context")
    assert context.status_code == 200
    assert context.json()["preferred_marketplaces"] == ["saturn"]


def test_user_profile_api_get_creates_empty_profile():
    client.post("/api/v1/user-profiles/clear")

    response = client.get("/api/v1/user-profiles/new-user")

    assert response.status_code == 200
    assert response.json()["user_id"] == "new-user"
