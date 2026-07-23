from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers

# SCALE-007 Part 1: shared/persistent DB -- no /clear, membership check via
# GET /pending instead of an actual claim (same reasoning as
# test_rc71_dead_letter_queue_vertical_slice.py: a replayed item's old
# created_at makes it a prime target for ANY concurrently-running test's
# unrelated claim-next() call, so an actual claim here would be flaky under
# `pytest -n auto`).


def test_rc72_vertical_slice_dead_letter_replay_with_audit_then_claim():
    with TestClient(app) as client:
        headers = operator_headers(client)

        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc72-user",
                "title": "RC72 vertical",
                "message": "DLQ audit replay",
                "payload": {"source": "rc72"},
            },
            headers=internal_service_headers(),
        ).json()

        for _ in range(3):
            client.post(
                "/api/v1/notification-outbox/claim-next",
                json={"worker_id": "worker-rc72-vertical"},
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

        replayed = client.post(
            f"/api/v1/notification-outbox/dead-letters/{queued['id']}/replay",
            headers=headers,
            json={
                "replay_reason": "operator_reviewed",
                "replayed_by": "rc72-admin",
            },
        ).json()

        assert replayed["item"]["status"] == "PENDING"
        assert replayed["item"]["payload"]["dlq_replay"]["reason"] == "operator_reviewed"

        pending = client.get(
            "/api/v1/notification-outbox/pending?limit=200", headers=headers
        ).json()

    pending_by_id = {item["id"]: item for item in pending["items"]}
    assert queued["id"] in pending_by_id
    assert pending_by_id[queued["id"]]["payload"]["dlq_replay"]["reason"] == "operator_reviewed"
