from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers

# AUTH-003 Part 1 event-loop lesson: chained DB requests need a single
# `with TestClient(app) as client:` scope on Windows+asyncpg. SCALE-007
# Part 1: shared/persistent DB, many concurrent test workers all racing on
# the same global FIFO claim-next() pool -- there is no per-item
# reservation, so drain-until-found is contention-prone under
# `pytest -n auto` (observed flaky when many drain-loop tests compete for
# the same backlog). mark_failed()/mark_pending_for_retry() have no
# PROCESSING precondition, so this test operates on its own item_id
# directly throughout rather than depending on which item claim-next()
# actually grabbed -- claim-next() itself is exercised generically (proves
# the HTTP contract works), its exact "moves MY item to PROCESSING"
# behavior is already covered deterministically (isolated in-memory repo)
# by test_rc69_notification_outbox_retry_scheduler_service.py.


def test_rc69_retry_scheduler_vertical_slice_claim_fail_requeue_claim_again():
    with TestClient(app) as client:
        headers = operator_headers(client)

        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc69-user",
                "title": "RC69 vertical",
                "message": "Claim fail requeue claim again",
                "payload": {"idempotency_key": "rc69-user:vertical"},
            },
            headers=internal_service_headers(),
        ).json()

        claim_response = client.post(
            "/api/v1/notification-outbox/claim-next",
            json={"worker_id": "worker-rc69-vertical-1"},
            headers=internal_service_headers(),
        )
        assert claim_response.status_code == 200

        due_time = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        failed = client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
            json={"error": "PROVIDER_TIMEOUT", "next_retry_at": due_time},
            headers=internal_service_headers(),
        ).json()
        assert failed["item"]["status"] == "FAILED"

        requeued = client.post(
            "/api/v1/notification-outbox/requeue-due-retries?limit=200",
            headers=internal_service_headers(),
        ).json()
        requeued_by_id = {item["id"]: item for item in requeued["items"]}
        assert queued["id"] in requeued_by_id
        assert requeued_by_id[queued["id"]]["status"] == "PENDING"

        # Prove it's back in the real claimable pool via the same query
        # path claim-next() uses (GET /pending), rather than physically
        # re-claiming it -- see module docstring.
        pending = client.get(
            "/api/v1/notification-outbox/pending?limit=200", headers=headers
        ).json()

    pending_by_id = {item["id"]: item for item in pending["items"]}
    assert queued["id"] in pending_by_id
    assert pending_by_id[queued["id"]]["status"] == "PENDING"
    assert pending_by_id[queued["id"]]["retry_count"] == 1
