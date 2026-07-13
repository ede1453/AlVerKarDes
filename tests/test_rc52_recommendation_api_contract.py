from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_recommendation_api_generates_recommendations():
    response = client.post(
        "/api/v1/recommendations/recommend",
        json={
            "query": "MacBook Air",
            "user_id": "user-1",
            "candidates": [
                {"product_key": "macbook-air-1", "product_name": "MacBook Air Amazon", "marketplace": "amazon", "price": "999.00"},
                {"product_key": "macbook-air-2", "product_name": "MacBook Air Saturn", "marketplace": "saturn", "price": "949.00", "canonical_confidence": 95},
            ],
            "personalization": {"top_offer": {"marketplace": "saturn"}},
            "deal_detection": {"deal_level": "EXCELLENT_DEAL"},
            "discount_intelligence": {"discount_quality": "EXCELLENT_REAL_DISCOUNT", "fake_discount_risk": "LOW"},
            "price_prediction": {"recommendation_hint": "BUY_SOON"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["items"][0]["recommendation_type"] == "BEST_CHOICE"


def test_recommendation_cached_api_returns_cache_metadata():
    response = client.post(
        "/api/v1/recommendations/recommend-cached",
        json={
            "query": "MacBook Air",
            "candidates": [{"product_key": "macbook-air", "product_name": "MacBook Air", "price": "949.00"}],
            "ttl_seconds": 300,
        },
    )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
