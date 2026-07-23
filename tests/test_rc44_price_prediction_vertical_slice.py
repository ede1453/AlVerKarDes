from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers


def test_price_prediction_vertical_slice_from_price_history_summary():
    # VISION-003: this used to build its price_history input via the
    # standalone price_history domain's /clear + /points/bulk + /summary
    # endpoints -- that domain was archived (no production caller, its only
    # real consumer was the also-archived ai_shopping_agent; the platform's
    # real price history is market.Price, unrelated to this test's scope).
    # The exact summary shape (min/max/average/latest/trend) this scenario
    # produced is reproduced directly here; price_prediction only cares that
    # `points` has >= 2 entries (for its MULTIPLE_PRICE_POINTS confidence
    # bump), not their content, so placeholders are fine.
    price_history_summary = {
        "product_key": "macbook-air",
        "currency": "EUR",
        "point_count": 2,
        "min_price": "949.00",
        "max_price": "999.00",
        "average_price": "974.00",
        "latest_price": "949.00",
        "trend": "DOWN",
        "points": [{"marketplace": "amazon"}, {"marketplace": "saturn"}],
    }

    with TestClient(app) as client:
        headers = auth_headers(client)
        prediction_response = client.post(
            "/api/v1/price-prediction/predict",
            headers=headers,
            json={
                "product_key": "macbook-air",
                "price_history": price_history_summary,
                "prediction_horizon_days": 7,
            },
        )

    assert prediction_response.status_code == 200
    data = prediction_response.json()
    assert data["product_key"] == "macbook-air"
    assert data["recommendation_hint"] in ["BUY_SOON", "WAIT_OR_WATCH", "WATCH"]
