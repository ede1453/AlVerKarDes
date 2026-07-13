from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_dead_letter(index: int):
    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc75-user",
            "title": f"RC75 vertical {index}",
            "message": "Circuit breaker vertical",
            "payload": {"source": "rc75"},
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


def test_rc75_vertical_slice_circuit_breaker_opens_after_dlq_spike():
    client.post("/api/v1/notification-outbox/clear")

    for index in range(3):
        _make_dead_letter(index)

    status = client.get(
        "/api/v1/notification-outbox/circuit-breaker/status",
        params={"failure_threshold": 3},
    ).json()

    assert status["status"] == "OPEN"
    assert status["failure_count"] == 3

    decision = client.get(
        "/api/v1/notification-outbox/circuit-breaker/can-deliver",
        params={"failure_threshold": 3},
    ).json()

    assert decision["allowed"] is False
    assert decision["reason"] == "CIRCUIT_BREAKER_OPEN"
