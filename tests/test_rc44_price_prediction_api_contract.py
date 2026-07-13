from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_price_prediction_api_predicts_price():
    response = client.post(
        "/api/v1/price-prediction/predict",
        json={
            "product_key": "macbook-air",
            "price_history": {
                "latest_price": "949.00",
                "min_price": "949.00",
                "average_price": "999.00",
                "max_price": "1099.00",
                "trend": "DOWN",
                "points": [{"price": "999.00"}, {"price": "949.00"}],
            },
            "prediction_horizon_days": 7,
        },
    )

    assert response.status_code == 200
    assert response.json()["recommendation_hint"] == "BUY_SOON"


def test_price_prediction_cached_api_returns_cache_metadata():
    response = client.post(
        "/api/v1/price-prediction/predict-cached",
        json={
            "product_key": "macbook-air",
            "price_history": {"latest_price": "949.00", "points": [{"price": "949.00"}]},
            "ttl_seconds": 300,
        },
    )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
