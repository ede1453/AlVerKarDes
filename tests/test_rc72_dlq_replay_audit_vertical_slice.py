from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc72_vertical_slice_dead_letter_replay_with_audit_then_claim():
    client.post("/api/v1/notification-outbox/clear")

    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc72-user",
            "title": "RC72 vertical",
            "message": "DLQ audit replay",
            "payload": {"source": "rc72"},
        },
    ).json()

    for _ in range(3):
        client.post("/api/v1/notification-outbox/claim-next")
        failed = client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
            json={
                "error": "PROVIDER_TIMEOUT",
                "next_retry_at": "2000-01-01T00:00:00+00:00",
            },
        ).json()
        if failed["item"]["status"] != "DEAD_LETTER":
            client.post("/api/v1/notification-outbox/requeue-due-retries")

    replayed = client.post(
        f"/api/v1/notification-outbox/dead-letters/{queued['id']}/replay",
        json={
            "replay_reason": "operator_reviewed",
            "replayed_by": "rc72-admin",
        },
    ).json()

    assert replayed["item"]["status"] == "PENDING"

    claimed = client.post("/api/v1/notification-outbox/claim-next").json()

    assert claimed["claimed"] is True
    assert claimed["item"]["id"] == queued["id"]
    assert claimed["item"]["payload"]["dlq_replay"]["reason"] == "operator_reviewed"
