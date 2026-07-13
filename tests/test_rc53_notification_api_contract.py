from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_notification_api_deliver():
    response = client.post(
        "/api/v1/notifications/deliver",
        json={
            "user_id": "user-1",
            "channels": ["in_app"],
            "title": "Strong deal detected",
            "message": "MacBook Air has strong buy signals.",
            "payload": {"product_key": "macbook-air"},
        },
    )

    assert response.status_code == 200
    assert response.json()["delivered_count"] == 1


def test_notification_api_from_smart_alert():
    response = client.post(
        "/api/v1/notifications/from-smart-alert",
        json={
            "user_id": "user-1",
            "smart_alert": {
                "title": "Strong deal detected",
                "message": "This product currently has strong buy signals.",
                "channels": ["in_app"],
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["delivered_count"] == 1
