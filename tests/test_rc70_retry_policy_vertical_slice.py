from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

# SCALE-007 Part 1: this suite runs against a real, shared, persistent dev
# database -- POST /clear would wipe rows other parallel tests depend on, so
# it's no longer used here. Assertions check membership/absence of our own
# item_id instead of exclusive-table-state counts (same discipline as
# test_rc34_job_queue_api_contract.py).


def test_rc70_vertical_slice_fail_with_backoff_then_scheduler_waits():
    with TestClient(app) as client:
        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc70-user",
                "title": "RC70 vertical",
                "message": "Backoff waits",
                "payload": {"source": "rc70"},
            },
            headers=internal_service_headers(),
        ).json()

        client.post(
            "/api/v1/notification-outbox/claim-next",
            json={"worker_id": "worker-rc70-vertical-1"},
            headers=internal_service_headers(),
        )

        failed = client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
            json={"error": "PROVIDER_TIMEOUT"},
            headers=internal_service_headers(),
        ).json()

        assert failed["item"]["status"] == "FAILED"
        assert failed["item"]["next_retry_at"] is not None

        requeue = client.post(
            "/api/v1/notification-outbox/requeue-due-retries?limit=200",
            headers=internal_service_headers(),
        ).json()

        requeued_ids = [item["id"] for item in requeue["items"]]
        assert queued["id"] not in requeued_ids


def test_rc70_vertical_slice_explicit_due_time_still_requeues_immediately():
    with TestClient(app) as client:
        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc70-user",
                "title": "RC70 vertical",
                "message": "Explicit due compatibility",
                "payload": {"source": "rc70"},
            },
            headers=internal_service_headers(),
        ).json()

        client.post(
            "/api/v1/notification-outbox/claim-next",
            json={"worker_id": "worker-rc70-vertical-2"},
            headers=internal_service_headers(),
        )

        client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
            json={
                "error": "PROVIDER_TIMEOUT",
                "next_retry_at": "2000-01-01T00:00:00+00:00",
            },
            headers=internal_service_headers(),
        )

        requeue = client.post(
            "/api/v1/notification-outbox/requeue-due-retries?limit=200",
            headers=internal_service_headers(),
        ).json()

        requeued_by_id = {item["id"]: item for item in requeue["items"]}
        assert queued["id"] in requeued_by_id
        assert requeued_by_id[queued["id"]]["status"] == "PENDING"
