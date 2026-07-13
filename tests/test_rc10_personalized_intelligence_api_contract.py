from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_personalized_intelligence_api_saves_profile_and_personalizes():
    profile_response = client.post(
        "/api/v1/personalized-intelligence/profiles",
        json={
            "user_id": "user-1",
            "preferred_brands": ["apple"],
            "price_sensitivity": "MEDIUM",
            "minimum_confidence": 70,
        },
    )

    assert profile_response.status_code == 200

    decision_response = client.post(
        "/api/v1/personalized-intelligence/decisions/personalize",
        json={
            "user_id": "user-1",
            "final_decision": "BUY_NOW",
            "confidence": 90,
            "product_brand": "apple",
            "opportunity_level": "HIGH",
        },
    )

    assert decision_response.status_code == 200
    assert decision_response.json()["personalized_confidence"] == 95


def test_personalized_intelligence_api_gets_profile():
    client.post(
        "/api/v1/personalized-intelligence/profiles",
        json={
            "user_id": "user-2",
            "avoided_brands": ["brand-x"],
            "price_sensitivity": "HIGH",
            "minimum_confidence": 80,
        },
    )

    response = client.get("/api/v1/personalized-intelligence/profiles/user-2")

    assert response.status_code == 200
    assert response.json()["price_sensitivity"] == "HIGH"
