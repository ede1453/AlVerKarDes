from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_deal_detection_api_detects_deal():
    response = client.post(
        "/api/v1/deal-detection/detect",
        json={
            "product_key": "macbook-air",
            "offer": {"price": "949.00", "marketplace": "saturn"},
            "price_history": {"min_price": "949.00", "average_price": "999.00", "latest_price": "949.00", "trend": "DOWN"},
            "personalization": {"top_offer": {"personalization_score": 95}},
        },
    )

    assert response.status_code == 200
    assert response.json()["deal_level"] == "EXCELLENT_DEAL"


def test_deal_detection_cached_api_returns_cache_metadata():
    response = client.post(
        "/api/v1/deal-detection/detect-cached",
        json={
            "product_key": "macbook-air",
            "offer": {"price": "949.00", "marketplace": "saturn"},
            "ttl_seconds": 300,
        },
    )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
