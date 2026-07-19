from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_personalized_intelligence_api_saves_profile_and_personalizes():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        profile_response = client.post(
            "/api/v1/personalized-intelligence/profiles",
            headers=headers,
            json={
                "user_id": user_id,
                "preferred_brands": ["apple"],
                "price_sensitivity": "MEDIUM",
                "minimum_confidence": 70,
            },
        )

        assert profile_response.status_code == 200

        decision_response = client.post(
            "/api/v1/personalized-intelligence/decisions/personalize",
            headers=headers,
            json={
                "user_id": user_id,
                "final_decision": "BUY_NOW",
                "confidence": 90,
                "product_brand": "apple",
                "opportunity_level": "HIGH",
            },
        )

    assert decision_response.status_code == 200
    assert decision_response.json()["personalized_confidence"] == 95


def test_personalized_intelligence_api_gets_profile():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post(
            "/api/v1/personalized-intelligence/profiles",
            headers=headers,
            json={
                "user_id": user_id,
                "avoided_brands": ["brand-x"],
                "price_sensitivity": "HIGH",
                "minimum_confidence": 80,
            },
        )

        response = client.get(
            f"/api/v1/personalized-intelligence/profiles/{user_id}", headers=headers
        )

    assert response.status_code == 200
    assert response.json()["price_sensitivity"] == "HIGH"
