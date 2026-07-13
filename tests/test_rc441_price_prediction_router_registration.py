from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc441_price_prediction_router_is_registered():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/price-prediction/predict" in paths
    assert "/api/v1/price-prediction/predict-cached" in paths


def test_rc441_price_prediction_endpoint_no_longer_returns_404():
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
    assert response.json()["product_key"] == "macbook-air"
