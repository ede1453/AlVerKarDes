from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_shopping_assistant_api_returns_advice():
    response = client.post(
        "/api/v1/ai-shopping-assistant/advise",
        json={
            "user_id": "user-1",
            "query": "Should I buy this MacBook?",
            "product_name": "MacBook Air",
            "product_brand": "apple",
            "current_price": "849.00",
            "currency": "EUR",
            "final_decision": "BUY_NOW",
            "confidence": 94,
            "risk_level": "LOW",
            "opportunity_level": "HIGH",
            "reason_codes": ["STRONG_BUY_SIGNAL"],
            "trust_score": 90,
            "community_score": 88,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["assistant_decision"] == "BUY_NOW"
    assert data["headline"] == "Buy MacBook Air now"
    assert data["next_actions"]
    assert data["assistant_context"]["user_id"] == "user-1"


def test_ai_shopping_assistant_api_blocks_high_risk():
    response = client.post(
        "/api/v1/ai-shopping-assistant/advise",
        json={
            "product_name": "Unknown Laptop",
            "final_decision": "BUY_NOW",
            "confidence": 96,
            "risk_level": "HIGH",
            "trust_score": 20,
        },
    )

    assert response.status_code == 200
    assert response.json()["assistant_decision"] == "DO_NOT_BUY"
