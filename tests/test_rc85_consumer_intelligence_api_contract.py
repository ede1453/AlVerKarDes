from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_consumer_intelligence_api_returns_buy_now():
    response = client.post(
        "/api/v1/consumer-intelligence/evaluate",
        json={
            "deal_score": 95,
            "authenticity_score": 96,
            "recommendation": "BUY_NOW",
            "recommendation_confidence": 94,
            "trend_direction": "DOWN",
            "store_trust_score": 90,
            "stock_status": "in_stock",
            "reason_codes": ["HIGH_DEAL_SCORE", "AUTHENTIC_DISCOUNT"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["final_decision"] == "BUY_NOW"
    assert data["risk_level"] == "LOW"
    assert data["opportunity_level"] == "HIGH"
    assert "STRONG_BUY_SIGNAL" in data["reason_codes"]


def test_consumer_intelligence_api_returns_do_not_buy():
    response = client.post(
        "/api/v1/consumer-intelligence/evaluate",
        json={
            "deal_score": 98,
            "authenticity_score": 20,
            "recommendation": "AVOID",
            "recommendation_confidence": 90,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["final_decision"] == "DO_NOT_BUY"
    assert data["risk_level"] == "HIGH"
