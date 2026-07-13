from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc150_rc154_vertical_slice():
    client.post("/api/v1/deal-operations/clear")

    client.post(
        "/api/v1/deal-operations/watchlist",
        json={
            "user_id":"user-1",
            "product_key":"apple::macbook-air::m5",
            "target_price":750,
            "minimum_confidence":70,
        },
    )

    response = client.post(
        "/api/v1/deal-operations/evaluate",
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
        f"/api/v1/deal-operations/opportunities/{opportunity_id}/decisions"
    ).json()

    assert history["decision_count"] == 1
