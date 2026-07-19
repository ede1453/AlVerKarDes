from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_user_profile_api_preferences_feedback_and_context():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post("/api/v1/user-profiles/clear", headers=headers)

        preferences = client.post(
            "/api/v1/user-profiles/preferences",
            headers=headers,
            json={
                "user_id": user_id,
                "preferred_marketplaces": ["saturn"],
                "preferred_brands": ["Apple"],
                "risk_tolerance": "LOW",
            },
        )
        assert preferences.status_code == 200
        assert preferences.json()["preferred_marketplaces"] == ["saturn"]

        merge = client.post(
            "/api/v1/user-profiles/feedback/merge",
            headers=headers,
            json={
                "user_id": user_id,
                "feedback_summary": {
                    "event_count": 2,
                    "preferred_product_keys": ["macbook-air"],
                    "avoided_product_keys": ["iphone"],
                },
            },
        )
        assert merge.status_code == 200
        assert merge.json()["preferred_product_keys"] == ["macbook-air"]

        context = client.get(
            f"/api/v1/user-profiles/{user_id}/recommendation-context", headers=headers
        )

    assert context.status_code == 200
    assert context.json()["preferred_marketplaces"] == ["saturn"]


def test_user_profile_api_get_creates_empty_profile():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post("/api/v1/user-profiles/clear", headers=headers)

        response = client.get(f"/api/v1/user-profiles/{user_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["user_id"] == user_id
