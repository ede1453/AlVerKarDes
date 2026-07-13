from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_discount_intelligence_vertical_slice_from_deal_prediction_price_history():
    client.post("/api/v1/events/clear")

    price_history = {
        "latest_price": "949.00",
        "min_price": "949.00",
        "average_price": "999.00",
        "max_price": "1099.00",
        "trend": "DOWN",
        "points": [{"price": "999.00"}, {"price": "949.00"}],
    }

    deal_response = client.post(
        "/api/v1/deal-detection/detect",
        json={
            "product_key": "macbook-air",
            "offer": {"price": "949.00", "marketplace": "saturn"},
            "price_history": price_history,
            "personalization": {"top_offer": {"personalization_score": 95}},
        },
    )
    assert deal_response.status_code == 200

    prediction_response = client.post(
        "/api/v1/price-prediction/predict",
        json={"product_key": "macbook-air", "price_history": price_history},
    )
    assert prediction_response.status_code == 200

    discount_response = client.post(
        "/api/v1/discount-intelligence/analyze",
        json={
            "product_key": "macbook-air",
            "current_price": "949.00",
            "claimed_original_price": "1099.00",
            "price_history": price_history,
            "deal_detection": deal_response.json(),
            "price_prediction": prediction_response.json(),
        },
    )

    assert discount_response.status_code == 200
    assert discount_response.json()["fake_discount_risk"] == "LOW"

    event_response = client.get("/api/v1/events?event_type=discount_intelligence.analyzed&source=discount_intelligence")
    assert event_response.status_code == 200
    assert event_response.json()["items"]
