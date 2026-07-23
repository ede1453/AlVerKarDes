from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers

# SCALE-007 Part 1: shared/persistent DB -- no /clear. dead_letter_count is
# a GLOBAL gauge that is NOT strictly monotonic (another concurrently-
# running test's replay_dead_letter() call moves an item back to PENDING,
# decreasing it) -- a threshold computed from a baseline read long before
# the final check (spanning our own 3-dead-letter creation, itself several
# HTTP round-trips) left a wide window for that to happen, observed flaky
# under `pytest -n auto`. Re-measuring the threshold as late as possible
# (immediately before the status check, right after our own dead letters
# exist) shrinks that window to two back-to-back calls instead of the
# whole test body.


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

        for index in range(3):
            _make_dead_letter(client, index)

        # Measured as late as possible (see module docstring) -- this is
        # guaranteed to include our own 3 dead letters, whatever else is
        # concurrently true globally.
        threshold = client.get(
            "/api/v1/notification-outbox/metrics", headers=headers
        ).json()["dead_letter_count"]

        status = client.get(
            "/api/v1/notification-outbox/circuit-breaker/status",
            headers=headers,
            params={"failure_threshold": threshold},
        ).json()

        assert status["status"] == "OPEN"
        assert status["failure_count"] >= threshold

        decision = client.get(
            "/api/v1/notification-outbox/circuit-breaker/can-deliver",
            headers=internal_service_headers(),
            params={"failure_threshold": threshold},
        ).json()

    assert decision["allowed"] is False
    assert decision["reason"] == "CIRCUIT_BREAKER_OPEN"
