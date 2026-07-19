from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_rc561_profile_aware_recommendation_reads_profile_api_state():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post("/api/v1/user-profiles/clear", headers=headers)

        pref_response = client.post(
            "/api/v1/user-profiles/preferences",
            headers=headers,
            json={
                "user_id": user_id,
                "preferred_marketplaces": ["saturn"],
                "preferred_brands": ["Apple"],
                "risk_tolerance": "LOW",
            },
        )
        assert pref_response.status_code == 200

        merge_response = client.post(
            "/api/v1/user-profiles/feedback/merge",
            headers=headers,
            json={
                "user_id": user_id,
                "feedback_summary": {
                    "event_count": 1,
                    "preferred_product_keys": ["macbook-air"],
                    "avoided_product_keys": [],
                },
            },
        )
        assert merge_response.status_code == 200

        response = client.post(
            "/api/v1/profile-aware-recommendations/recommend",
            headers=headers,
            json={
                "user_id": user_id,
                "query": "MacBook Air",
                "candidates": [
                    {
                        "product_key": "macbook-air",
                        "product_name": "Apple MacBook Air",
                        "marketplace": "saturn",
                        "price": "949.00",
                    }
                ],
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert data["profile_context"]["preferred_marketplaces"] == ["saturn"]
    assert data["profile_context"]["preferred_brands"] == ["Apple"]
    assert data["profile_context"]["preferred_product_keys"] == ["macbook-air"]
    assert data["items"][0]["score"] >= 80
