from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc145_rc149_vertical_slice():
    response = client.post(
        "/api/v1/deal-intelligence/evaluate",
        json={
            "opportunities":[
                {
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
                },
                {
                    "source_id":"ebay",
                    "canonical_product_key":"apple::macbook-air::m5",
                    "price":900,
                    "claimed_original_price":1000,
                    "historical_prices":[950,1000,1050,980],
                    "source_confidence":70,
                    "freshness_status":"AGING",
                    "anomaly_detected":False,
                    "review_reliability":60,
                    "effective_price":920
                }
            ]
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["evaluated_count"] == 2
    assert data["recommendation"]["decision"] == "BUY"
