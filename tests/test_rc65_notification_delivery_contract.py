from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_rc65_notification_deliver_contract_still_works():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        response = client.post(
            "/api/v1/notifications/deliver",
            headers=headers,
            json={
                "user_id": user_id,
                "channels": ["in_app"],
                "title": "RC65 notification",
                "message": "Notification delivery contract check.",
                "payload": {"source": "rc65"},
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == user_id
    assert data["requested_channels"] == ["in_app"]
    assert data["delivered_count"] >= 1
    assert data["failed_count"] == 0
    assert len(data["messages"]) >= 1

    first = data["messages"][0]
    assert first["channel"] == "in_app"
    assert first["status"] in {"DELIVERED", "QUEUED"}
    assert first["provider"] in {"mock", "external"}


def test_rc65_notification_from_smart_alert_contract_still_works():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        response = client.post(
            "/api/v1/notifications/from-smart-alert",
            headers=headers,
            json={
                "user_id": user_id,
                "smart_alert": {
                    "alert_id": "rc65-alert",
                    "user_id": user_id,
                    "product_key": "macbook-air",
                    "should_alert": True,
                    "alert_level": "URGENT",
                    "alert_score": 95,
                    "title": "Strong deal detected",
                    "message": "MacBook Air has strong buy signals.",
                    "channels": ["in_app"],
                    "reasons": ["RC65_SMOKE"],
                    "metadata": {"source": "rc65"},
                },
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == user_id
    assert data["delivered_count"] >= 1
    assert data["failed_count"] == 0
