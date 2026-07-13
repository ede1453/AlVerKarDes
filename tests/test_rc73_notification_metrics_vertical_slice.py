from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc73_vertical_slice_metrics_across_lifecycle():
    client.post("/api/v1/notification-outbox/clear")

    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc73-user",
            "title": "RC73 vertical",
            "message": "Metrics lifecycle",
        },
    ).json()

    initial = client.get("/api/v1/notification-outbox/metrics").json()
    assert initial["pending_count"] == 1

    client.post("/api/v1/notification-outbox/claim-next")
    processing = client.get("/api/v1/notification-outbox/metrics").json()
    assert processing["processing_count"] == 1

    client.post(f"/api/v1/notification-outbox/{queued['id']}/mark-delivered")
    delivered = client.get("/api/v1/notification-outbox/metrics").json()

    assert delivered["delivered_count"] == 1
    assert delivered["delivery_success_rate"] == 1.0
