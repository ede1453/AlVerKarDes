from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_profile_aware_vertical_slice_from_profile_store():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post("/api/v1/user-profiles/clear", headers=headers)

        client.post(
            "/api/v1/user-profiles/preferences",
            headers=headers,
            json={
                "user_id": user_id,
                "preferred_marketplaces": ["saturn"],
                "preferred_brands": ["Apple"],
                "risk_tolerance": "LOW",
            },
        )

        client.post(
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
    assert response.json()["profile_context"]["preferred_marketplaces"] == ["saturn"]
    assert response.json()["items"][0]["score"] >= 80
