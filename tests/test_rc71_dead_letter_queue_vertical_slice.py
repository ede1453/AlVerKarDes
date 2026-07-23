from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers

# SCALE-007 Part 1: shared/persistent DB -- no /clear, membership checks
# instead of exclusive-table-state counts, drain-until-found for the final
# claim (same discipline as test_rc34_job_queue_api_contract.py).


def test_rc71_vertical_slice_fail_to_dead_letter_then_replay_and_claim():
    with TestClient(app) as client:
        headers = operator_headers(client)

        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc71-user",
                "title": "RC71 vertical",
                "message": "DLQ replay",
                "payload": {"idempotency_key": "rc71-user:vertical"},
            },
            headers=internal_service_headers(),
        ).json()

        for _ in range(3):
            client.post(
                "/api/v1/notification-outbox/claim-next",
                json={"worker_id": "worker-rc71-vertical"},
                headers=internal_service_headers(),
            )
            failed = client.post(
                f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
                json={
                    "error": "PROVIDER_TIMEOUT",
                    "next_retry_at": "2000-01-01T00:00:00+00:00",
                },
                headers=internal_service_headers(),
            ).json()

            if failed["item"]["status"] != "DEAD_LETTER":
                client.post(
                    "/api/v1/notification-outbox/requeue-due-retries?limit=200",
                    headers=internal_service_headers(),
                )

        dead_letters = client.get(
            "/api/v1/notification-outbox/dead-letters?limit=200", headers=headers
        ).json()
        dead_letter_ids = [item["id"] for item in dead_letters["items"]]
        assert queued["id"] in dead_letter_ids

        replayed = client.post(
            f"/api/v1/notification-outbox/dead-letters/{queued['id']}/replay",
            headers=headers,
        ).json()
        assert replayed["item"]["status"] == "PENDING"

        # Prove it re-entered the real claimable pool via the same query
        # path claim-next() uses (GET /pending), rather than physically
        # claiming it -- a replayed item's original (old) created_at makes
        # it a prime target for ANY concurrently-running test's unrelated
        # claim-next() call to grab first (shared/persistent DB, SCALE-007
        # Part 1: claim-next has no per-item reservation), so an actual
        # claim attempt here would be flaky under `pytest -n auto`.
        pending = client.get(
            "/api/v1/notification-outbox/pending?limit=200", headers=headers
        ).json()
        pending_by_id = {item["id"]: item for item in pending["items"]}
        assert queued["id"] in pending_by_id
        assert pending_by_id[queued["id"]]["status"] == "PENDING"
