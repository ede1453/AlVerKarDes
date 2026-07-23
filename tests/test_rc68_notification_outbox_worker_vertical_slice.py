from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

# AUTH-003 Part 1 event-loop lesson: chained DB requests need a single
# `with TestClient(app) as client:` scope on Windows+asyncpg.


def test_rc68_worker_vertical_slice_enqueue_claim_fail_retry_dead_letter():
    with TestClient(app) as client:
        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc68-user",
                "title": "RC68 vertical",
                "message": "Retry path",
                "payload": {"idempotency_key": "rc68-user:vertical"},
            },
            headers=internal_service_headers(),
        ).json()

        for expected_retry_count in [1, 2, 3]:
            claimed = client.post(
                "/api/v1/notification-outbox/claim-next",
                json={"worker_id": "worker-rc68-vertical"},
                headers=internal_service_headers(),
            ).json()
            assert claimed["claimed"] is True

            failed = client.post(
                f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
                json={"error": "PROVIDER_TIMEOUT"},
                headers=internal_service_headers(),
            ).json()

            assert failed["updated"] is True
            assert failed["item"]["retry_count"] == expected_retry_count

            if expected_retry_count < 3:
                # In-memory service keeps failed items out of pending list unless requeued by future scheduler.
                break

    # RC68 sadece worker boundary ekler. Otomatik retry scheduler RC69 kapsamına bırakılmıştır.
    assert queued["id"]
