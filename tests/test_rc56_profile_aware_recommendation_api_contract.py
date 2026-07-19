from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_profile_aware_recommendation_api_recommends_with_profile_context():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        response = client.post(
            "/api/v1/profile-aware-recommendations/recommend",
            headers=headers,
            json={
                "user_id": user_id,
                "query": "MacBook Air",
                "profile_context": {
                    "user_id": user_id,
                    "preferred_product_keys": ["macbook-air"],
                    "preferred_marketplaces": ["saturn"],
                    "preferred_brands": ["Apple"],
                    "avoided_product_keys": [],
                    "blocked_marketplaces": [],
                    "risk_tolerance": "LOW",
                    "profile_score": 60,
                    "metadata": {"context_version": "user_profile_context_v1"},
                },
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
    assert response.json()["items"][0]["profile_context_applied"] is True
