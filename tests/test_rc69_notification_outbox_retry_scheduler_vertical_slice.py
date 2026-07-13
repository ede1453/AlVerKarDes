from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc69_retry_scheduler_vertical_slice_claim_fail_requeue_claim_again():
    client.post("/api/v1/notification-outbox/clear")

    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc69-user",
            "title": "RC69 vertical",
            "message": "Claim fail requeue claim again",
            "payload": {"idempotency_key": "rc69-user:vertical"},
        },
    ).json()

    first_claim = client.post("/api/v1/notification-outbox/claim-next").json()
    assert first_claim["claimed"] is True
    assert first_claim["item"]["status"] == "PROCESSING"

    due_time = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    failed = client.post(
        f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
        json={"error": "PROVIDER_TIMEOUT", "next_retry_at": due_time},
    ).json()
    assert failed["item"]["status"] == "FAILED"

    requeued = client.post("/api/v1/notification-outbox/requeue-due-retries").json()
    assert requeued["requeued_count"] == 1

    second_claim = client.post("/api/v1/notification-outbox/claim-next").json()
    assert second_claim["claimed"] is True
    assert second_claim["item"]["id"] == queued["id"]
    assert second_claim["item"]["status"] == "PROCESSING"
    assert second_claim["item"]["retry_count"] == 1
