from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc70_vertical_slice_fail_with_backoff_then_scheduler_waits():
    client.post("/api/v1/notification-outbox/clear")

    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc70-user",
            "title": "RC70 vertical",
            "message": "Backoff waits",
            "payload": {"source": "rc70"},
        },
    ).json()

    client.post("/api/v1/notification-outbox/claim-next")

    failed = client.post(
        f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
        json={"error": "PROVIDER_TIMEOUT"},
    ).json()

    assert failed["item"]["status"] == "FAILED"
    assert failed["item"]["next_retry_at"] is not None

    requeue = client.post("/api/v1/notification-outbox/requeue-due-retries").json()

    assert requeue["requeued_count"] == 0


def test_rc70_vertical_slice_explicit_due_time_still_requeues_immediately():
    client.post("/api/v1/notification-outbox/clear")

    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc70-user",
            "title": "RC70 vertical",
            "message": "Explicit due compatibility",
            "payload": {"source": "rc70"},
        },
    ).json()

    client.post("/api/v1/notification-outbox/claim-next")

    client.post(
        f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
        json={
            "error": "PROVIDER_TIMEOUT",
            "next_retry_at": "2000-01-01T00:00:00+00:00",
        },
    )

    requeue = client.post("/api/v1/notification-outbox/requeue-due-retries").json()

    assert requeue["requeued_count"] == 1
    assert requeue["items"][0]["status"] == "PENDING"
