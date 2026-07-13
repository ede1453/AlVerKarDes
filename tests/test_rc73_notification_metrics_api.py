from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc73_notification_metrics_api_contract():
    client.post("/api/v1/notification-outbox/clear")

    client.post(
        "/api/v1/notification-outbox/enqueue",
        json={"user_id": "rc73-user", "title": "RC73", "message": "Metrics"},
    )

    response = client.get("/api/v1/notification-outbox/metrics")

    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 1
    assert data["pending_count"] == 1
    assert data["metadata"]["metrics_version"] == "notification_metrics_v1"


def test_rc73_notification_metrics_api_after_delivery():
    client.post("/api/v1/notification-outbox/clear")

    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={"user_id": "rc73-user", "title": "RC73", "message": "Delivered"},
    ).json()

    client.post("/api/v1/notification-outbox/claim-next")
    client.post(f"/api/v1/notification-outbox/{queued['id']}/mark-delivered")

    data = client.get("/api/v1/notification-outbox/metrics").json()

    assert data["delivered_count"] == 1
    assert data["delivery_success_rate"] == 1.0
