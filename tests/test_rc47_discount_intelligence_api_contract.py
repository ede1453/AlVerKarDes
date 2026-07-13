from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_discount_intelligence_api_analyzes_discount():
    response = client.post(
        "/api/v1/discount-intelligence/analyze",
        json={
            "product_key": "macbook-air",
            "current_price": "949.00",
            "claimed_original_price": "1099.00",
            "price_history": {"min_price": "949.00", "average_price": "999.00", "max_price": "1099.00", "trend": "DOWN"},
            "deal_detection": {"deal_score": 95},
            "price_prediction": {"recommendation_hint": "BUY_SOON"},
        },
    )

    assert response.status_code == 200
    assert response.json()["discount_quality"] == "EXCELLENT_REAL_DISCOUNT"


def test_discount_intelligence_cached_api_returns_cache_metadata():
    response = client.post(
        "/api/v1/discount-intelligence/analyze-cached",
        json={
            "product_key": "macbook-air",
            "current_price": "949.00",
            "claimed_original_price": "1099.00",
            "ttl_seconds": 300,
        },
    )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
