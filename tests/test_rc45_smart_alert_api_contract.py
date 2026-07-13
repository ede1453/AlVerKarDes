from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_smart_alert_api_evaluates_alert():
    response = client.post(
        "/api/v1/smart-alerts/evaluate",
        json={
            "user_id": "user-1",
            "product_key": "macbook-air",
            "deal_detection": {"deal_level": "EXCELLENT_DEAL", "deal_score": 95},
            "price_prediction": {"recommendation_hint": "BUY_SOON"},
            "personalization": {"top_offer": {"personalization_score": 95}},
            "channels": ["in_app"],
        },
    )

    assert response.status_code == 200
    assert response.json()["should_alert"] is True


def test_smart_alert_cached_api_returns_cache_metadata():
    response = client.post(
        "/api/v1/smart-alerts/evaluate-cached",
        json={
            "user_id": "user-1",
            "product_key": "macbook-air",
            "deal_detection": {"deal_level": "GOOD_DEAL", "deal_score": 80},
            "ttl_seconds": 300,
        },
    )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
