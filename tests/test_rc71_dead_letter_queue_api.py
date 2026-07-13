from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_dead_letter_item():
    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc71-user",
            "title": "RC71 API",
            "message": "Dead letter",
            "payload": {"source": "rc71"},
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


def test_rc71_dead_letter_list_api_contract():
    client.post("/api/v1/notification-outbox/clear")
    queued = _create_dead_letter_item()

    response = client.get("/api/v1/notification-outbox/dead-letters")

    assert response.status_code == 200
    data = response.json()

    assert data["dead_letter_count"] == 1
    assert data["items"][0]["id"] == queued["id"]
    assert data["items"][0]["status"] == "DEAD_LETTER"


def test_rc71_dead_letter_replay_api_contract():
    client.post("/api/v1/notification-outbox/clear")
    queued = _create_dead_letter_item()

    response = client.post(f"/api/v1/notification-outbox/dead-letters/{queued['id']}/replay")

    assert response.status_code == 200
    data = response.json()

    assert data["replayed"] is True
    assert data["item"]["status"] == "PENDING"
