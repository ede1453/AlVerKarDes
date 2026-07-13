from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_recommendation_intelligence_api_returns_explainable_buy_now():
    response = client.post(
        "/api/v1/recommendations/intelligence/evaluate",
        json={
            "deal_score": 95,
            "authenticity_score": 96,
            "trend_direction": "DOWN",
            "store_trust_score": 90,
            "stock_status": "in_stock",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["recommendation"] == "BUY_NOW"
    assert data["confidence"] >= 90
    assert "HIGH_DEAL_SCORE" in data["reason_codes"]
    assert "AUTHENTIC_DISCOUNT" in data["reason_codes"]
    assert data["explanation"]


def test_recommendation_intelligence_api_returns_avoid_for_fake_discount():
    response = client.post(
        "/api/v1/recommendations/intelligence/evaluate",
        json={
            "deal_score": 98,
            "authenticity_score": 20,
            "trend_direction": "DOWN",
            "store_trust_score": 95,
            "stock_status": "in_stock",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["recommendation"] == "AVOID"
    assert data["reason_codes"] == ["POSSIBLE_FAKE_DISCOUNT"]
