from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

# AUTH-003 Part 1 event-loop lesson: chained DB requests need a single
# `with TestClient(app) as client:` scope on Windows+asyncpg.


def test_rc69_outbox_requeue_due_retries_api_contract():
    # Shared/persistent DB (SCALE-007 Part 1) -- assert membership of our
    # own item rather than an exact requeued_count, since other tests'
    # due-for-retry items may legitimately be requeued in the same call.
    with TestClient(app) as client:
        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc69-user",
                "title": "RC69 API",
                "message": "Retry scheduler",
                "payload": {"source": "rc69"},
            },
            headers=internal_service_headers(),
        ).json()

        client.post(
            "/api/v1/notification-outbox/claim-next",
            json={"worker_id": "worker-rc69-api"},
            headers=internal_service_headers(),
        )
        due_time = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()

        failed = client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
            json={"error": "PROVIDER_TIMEOUT", "next_retry_at": due_time},
            headers=internal_service_headers(),
        )
        assert failed.status_code == 200

        response = client.post(
            "/api/v1/notification-outbox/requeue-due-retries?limit=200",
            headers=internal_service_headers(),
        )

    assert response.status_code == 200

    data = response.json()
    requeued = {item["id"]: item for item in data["items"]}
    assert queued["id"] in requeued
    assert requeued[queued["id"]]["status"] == "PENDING"


def test_rc69_outbox_requeue_due_retries_empty_api_contract():
    # A future-dated failure must never come back as requeued -- checked as
    # a specific-item exclusion (not a global empty-queue assumption, which
    # doesn't hold against a shared/persistent DB).
    with TestClient(app) as client:
        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc69-user",
                "title": "RC69 API Future",
                "message": "Not due yet",
            },
            headers=internal_service_headers(),
        ).json()

        client.post(
            "/api/v1/notification-outbox/claim-next",
            json={"worker_id": "worker-rc69-api-future"},
            headers=internal_service_headers(),
        )
        future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
            json={"error": "PROVIDER_TIMEOUT", "next_retry_at": future_time},
            headers=internal_service_headers(),
        )

        response = client.post(
            "/api/v1/notification-outbox/requeue-due-retries?limit=200",
            headers=internal_service_headers(),
        )

    assert response.status_code == 200
    data = response.json()

    requeued_ids = [item["id"] for item in data["items"]]
    assert queued["id"] not in requeued_ids
