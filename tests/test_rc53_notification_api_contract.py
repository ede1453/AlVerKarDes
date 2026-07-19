from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_notification_api_deliver():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        response = client.post(
            "/api/v1/notifications/deliver",
            headers=headers,
            json={
                "user_id": user_id,
                "channels": ["in_app"],
                "title": "Strong deal detected",
                "message": "MacBook Air has strong buy signals.",
                "payload": {"product_key": "macbook-air"},
            },
        )

    assert response.status_code == 200
    assert response.json()["delivered_count"] == 1


def test_notification_api_from_smart_alert():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        response = client.post(
            "/api/v1/notifications/from-smart-alert",
            headers=headers,
            json={
                "user_id": user_id,
                "smart_alert": {
                    "title": "Strong deal detected",
                    "message": "This product currently has strong buy signals.",
                    "channels": ["in_app"],
                },
            },
        )

    assert response.status_code == 200
    assert response.json()["delivered_count"] == 1
