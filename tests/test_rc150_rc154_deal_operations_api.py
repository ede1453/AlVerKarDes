from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

def test_rc150_rc154_vertical_slice():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/deal-operations/clear", headers=headers)

        client.post(
            "/api/v1/deal-operations/watchlist",
            headers=headers,
            json={
                "user_id":"user-1",
                "product_key":"apple::macbook-air::m5",
                "target_price":750,
                "minimum_confidence":70,
            },
        )

        response = client.post(
            "/api/v1/deal-operations/evaluate",
            headers=headers,
            json={
                "user_id":"user-1",
                "opportunities":[{
                    "source_id":"amazon",
                    "canonical_product_key":"apple::macbook-air::m5",
                    "price":700,
                    "claimed_original_price":1000,
                    "historical_prices":[950,1000,1050,980],
                    "source_confidence":90,
                    "freshness_status":"FRESH",
                    "anomaly_detected":False,
                    "review_reliability":80,
                    "effective_price":700
                }]
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["recommendation"]["decision"] == "BUY"
        assert data["alert"]["should_alert"] is True

        opportunity_id = data[
            "best_opportunity"
        ]["opportunity_id"]

        history = client.get(
            f"/api/v1/deal-operations/opportunities/{opportunity_id}/decisions",
            headers=headers,
        ).json()

    assert history["decision_count"] == 1
