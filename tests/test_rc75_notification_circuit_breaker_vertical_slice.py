from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers

# SCALE-007 Part 1: shared/persistent DB -- no /clear. The threshold is
# computed relative to the baseline dead_letter_count (from /metrics)
# instead of a fixed absolute value, so the "opens after N NEW dead
# letters" business rule stays provable regardless of leftover dead
# letters from other tests/runs.


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
            json={"worker_id": f"worker-rc75-vertical-{index}"},
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
                "/api/v1/notification-outbox/requeue-due-retries?limit=200",
                headers=internal_service_headers(),
            )


def test_rc75_vertical_slice_circuit_breaker_opens_after_dlq_spike():
    with TestClient(app) as client:
        headers = operator_headers(client)

        baseline_dead_letter_count = client.get(
            "/api/v1/notification-outbox/metrics", headers=headers
        ).json()["dead_letter_count"]

        for index in range(3):
            _make_dead_letter(client, index)

        threshold = baseline_dead_letter_count + 3

        status = client.get(
            "/api/v1/notification-outbox/circuit-breaker/status",
            headers=headers,
            params={"failure_threshold": threshold},
        ).json()

        assert status["status"] == "OPEN"
        # dead_letter_count is monotonically increasing and GLOBAL -- other
        # concurrently-running tests may add their own dead letters between
        # our baseline read and this one, so it can be >= our +3
        # contribution, not exactly threshold (observed flaky under
        # `pytest -n auto`). It can never be LESS than threshold, though,
        # since our own 3 dead letters are unconditionally included.
        assert status["failure_count"] >= threshold

        decision = client.get(
            "/api/v1/notification-outbox/circuit-breaker/can-deliver",
            headers=internal_service_headers(),
            params={"failure_threshold": threshold},
        ).json()

    assert decision["allowed"] is False
    assert decision["reason"] == "CIRCUIT_BREAKER_OPEN"
