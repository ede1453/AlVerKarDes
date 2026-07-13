from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_smart_alert_vertical_slice_from_deal_and_prediction():
    client.post("/api/v1/events/clear")

    deal_response = client.post(
        "/api/v1/deal-detection/detect",
        json={
            "product_key": "macbook-air",
            "offer": {"price": "949.00", "marketplace": "saturn"},
            "price_history": {"min_price": "949.00", "average_price": "999.00", "latest_price": "949.00", "trend": "DOWN"},
            "personalization": {"top_offer": {"personalization_score": 95}},
        },
    )
    assert deal_response.status_code == 200

    prediction_response = client.post(
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
        },
    )
    assert prediction_response.status_code == 200

    alert_response = client.post(
        "/api/v1/smart-alerts/evaluate",
        json={
            "user_id": "user-1",
            "product_key": "macbook-air",
            "deal_detection": deal_response.json(),
            "price_prediction": prediction_response.json(),
            "personalization": {"top_offer": {"personalization_score": 95}},
        },
    )

    assert alert_response.status_code == 200
    assert alert_response.json()["should_alert"] is True

    event_response = client.get("/api/v1/events?event_type=smart_alert.evaluated&source=smart_alerts")
    assert event_response.status_code == 200
    assert event_response.json()["items"]
