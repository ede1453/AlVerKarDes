from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc71_vertical_slice_fail_to_dead_letter_then_replay_and_claim():
    client.post("/api/v1/notification-outbox/clear")

    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc71-user",
            "title": "RC71 vertical",
            "message": "DLQ replay",
            "payload": {"idempotency_key": "rc71-user:vertical"},
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

    dead_letters = client.get("/api/v1/notification-outbox/dead-letters").json()
    assert dead_letters["dead_letter_count"] == 1

    replayed = client.post(
        f"/api/v1/notification-outbox/dead-letters/{queued['id']}/replay"
    ).json()
    assert replayed["item"]["status"] == "PENDING"

    claimed = client.post("/api/v1/notification-outbox/claim-next").json()
    assert claimed["claimed"] is True
    assert claimed["item"]["id"] == queued["id"]
