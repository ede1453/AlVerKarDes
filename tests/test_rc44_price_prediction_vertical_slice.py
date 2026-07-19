from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers


def test_price_prediction_vertical_slice_from_price_history_summary():
    with TestClient(app) as client:
        headers = auth_headers(client)
        client.post("/api/v1/price-history/clear", headers=headers)

        client.post(
            "/api/v1/price-history/points/bulk",
            headers=headers,
            json={
                "points": [
                    {"product_key": "macbook-air", "marketplace": "amazon", "price": "999.00", "currency": "EUR"},
                    {"product_key": "macbook-air", "marketplace": "saturn", "price": "949.00", "currency": "EUR"},
                ]
            },
        )

        summary_response = client.get(
            "/api/v1/price-history/macbook-air/summary", headers=headers
        )
        assert summary_response.status_code == 200

        prediction_response = client.post(
            "/api/v1/price-prediction/predict",
            headers=headers,
            json={
                "product_key": "macbook-air",
                "price_history": summary_response.json(),
                "prediction_horizon_days": 7,
            },
        )

    assert prediction_response.status_code == 200
    data = prediction_response.json()
    assert data["product_key"] == "macbook-air"
    assert data["recommendation_hint"] in ["BUY_SOON", "WAIT_OR_WATCH", "WATCH"]
