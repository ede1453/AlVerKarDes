from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def test_rc73_notification_metrics_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)

        client.post(
            "/api/v1/notification-outbox/enqueue",
            json={"user_id": "rc73-user", "title": "RC73", "message": "Metrics"},
            headers=internal_service_headers(),
        )

        response = client.get(
            "/api/v1/notification-outbox/metrics", headers=headers
        )

    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 1
    assert data["pending_count"] == 1
    assert data["metadata"]["metrics_version"] == "notification_metrics_v1"


def test_rc73_notification_metrics_api_after_delivery():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)

        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={"user_id": "rc73-user", "title": "RC73", "message": "Delivered"},
            headers=internal_service_headers(),
        ).json()

        client.post(
            "/api/v1/notification-outbox/claim-next",
            headers=internal_service_headers(),
        )
        client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-delivered",
            headers=internal_service_headers(),
        )

        data = client.get(
            "/api/v1/notification-outbox/metrics", headers=headers
        ).json()

    assert data["delivered_count"] == 1
    assert data["delivery_success_rate"] == 1.0
