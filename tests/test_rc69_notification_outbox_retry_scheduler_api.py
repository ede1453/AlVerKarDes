from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc69_outbox_requeue_due_retries_api_contract():
    client.post("/api/v1/notification-outbox/clear")

    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc69-user",
            "title": "RC69 API",
            "message": "Retry scheduler",
            "payload": {"source": "rc69"},
        },
    ).json()

    client.post("/api/v1/notification-outbox/claim-next")
    due_time = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()

    failed = client.post(
        f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
        json={"error": "PROVIDER_TIMEOUT", "next_retry_at": due_time},
    )
    assert failed.status_code == 200

    response = client.post("/api/v1/notification-outbox/requeue-due-retries")
    assert response.status_code == 200

    data = response.json()
    assert data["requeued_count"] == 1
    assert data["items"][0]["id"] == queued["id"]
    assert data["items"][0]["status"] == "PENDING"


def test_rc69_outbox_requeue_due_retries_empty_api_contract():
    client.post("/api/v1/notification-outbox/clear")

    response = client.post("/api/v1/notification-outbox/requeue-due-retries")

    assert response.status_code == 200
    data = response.json()

    assert data["requeued_count"] == 0
    assert data["items"] == []
