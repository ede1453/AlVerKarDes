from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def test_rc70_vertical_slice_fail_with_backoff_then_scheduler_waits():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)

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
            "/api/v1/notification-outbox/requeue-due-retries",
            headers=internal_service_headers(),
        ).json()

        assert requeue["requeued_count"] == 0


def test_rc70_vertical_slice_explicit_due_time_still_requeues_immediately():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)

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
            "/api/v1/notification-outbox/requeue-due-retries",
            headers=internal_service_headers(),
        ).json()

        assert requeue["requeued_count"] == 1
        assert requeue["items"][0]["status"] == "PENDING"
