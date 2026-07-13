from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_dead_letter_via_api() -> dict:
    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc72-user",
            "title": "RC72 API",
            "message": "DLQ replay audit",
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

    return queued


def test_rc72_replay_dead_letter_api_accepts_audit_payload():
    client.post("/api/v1/notification-outbox/clear")
    queued = _make_dead_letter_via_api()

    response = client.post(
        f"/api/v1/notification-outbox/dead-letters/{queued['id']}/replay",
        json={
            "replay_reason": "manual_admin_retry",
            "replayed_by": "rc72-admin",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["replayed"] is True
    assert data["item"]["status"] == "PENDING"
    assert data["item"]["payload"]["dlq_replay"]["reason"] == "manual_admin_retry"
    assert data["item"]["payload"]["dlq_replay"]["replayed_by"] == "rc72-admin"
