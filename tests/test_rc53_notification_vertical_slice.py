from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_notification_vertical_slice_from_smart_alert():
    alert_response = client.post(
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

    assert alert_response.status_code == 200
    alert = alert_response.json()
    assert alert["should_alert"] is True

    notification_response = client.post(
        "/api/v1/notifications/from-smart-alert",
        json={
            "user_id": "user-1",
            "smart_alert": alert,
        },
    )

    assert notification_response.status_code == 200
    assert notification_response.json()["delivered_count"] == 1
