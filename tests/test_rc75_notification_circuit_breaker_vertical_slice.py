from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def _make_dead_letter(client: TestClient, index: int):
    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        headers=internal_service_headers(),
        json={
            "user_id": "rc75-user",
            "title": f"RC75 vertical {index}",
            "message": "Circuit breaker vertical",
            "payload": {"source": "rc75"},
        },
    ).json()

    for _ in range(3):
        client.post(
            "/api/v1/notification-outbox/claim-next",
            headers=internal_service_headers(),
        )
        failed = client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
            headers=internal_service_headers(),
            json={
                "error": "PROVIDER_TIMEOUT",
                "next_retry_at": "2000-01-01T00:00:00+00:00",
            },
        ).json()

        if failed["item"]["status"] != "DEAD_LETTER":
            client.post(
                "/api/v1/notification-outbox/requeue-due-retries",
                headers=internal_service_headers(),
            )


def test_rc75_vertical_slice_circuit_breaker_opens_after_dlq_spike():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)

        for index in range(3):
            _make_dead_letter(client, index)

        status = client.get(
            "/api/v1/notification-outbox/circuit-breaker/status",
            headers=headers,
            params={"failure_threshold": 3},
        ).json()

        assert status["status"] == "OPEN"
        assert status["failure_count"] == 3

        decision = client.get(
            "/api/v1/notification-outbox/circuit-breaker/can-deliver",
            headers=internal_service_headers(),
            params={"failure_threshold": 3},
        ).json()

    assert decision["allowed"] is False
    assert decision["reason"] == "CIRCUIT_BREAKER_OPEN"
