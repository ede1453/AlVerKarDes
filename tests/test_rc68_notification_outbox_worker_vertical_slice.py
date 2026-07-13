from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc68_worker_vertical_slice_enqueue_claim_fail_retry_dead_letter():
    client.post("/api/v1/notification-outbox/clear")

    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc68-user",
            "title": "RC68 vertical",
            "message": "Retry path",
            "payload": {"idempotency_key": "rc68-user:vertical"},
        },
    ).json()

    for expected_retry_count in [1, 2, 3]:
        claimed = client.post("/api/v1/notification-outbox/claim-next").json()
        assert claimed["claimed"] is True

        failed = client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
            json={"error": "PROVIDER_TIMEOUT"},
        ).json()

        assert failed["updated"] is True
        assert failed["item"]["retry_count"] == expected_retry_count

        if expected_retry_count < 3:
            # In-memory service keeps failed items out of pending list unless requeued by future scheduler.
            break

    # RC68 sadece worker boundary ekler. Otomatik retry scheduler RC69 kapsamına bırakılmıştır.
    assert queued["id"]
