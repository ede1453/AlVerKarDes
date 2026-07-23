from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def test_rc68_outbox_enqueue_and_pending_api_contract():
    # This suite runs against a real, shared, persistent dev database under
    # parallel test workers (SCALE-007 Part 1 -- notification_outbox_items
    # is no longer per-process in-memory), so /clear + an exact pending_count
    # would race with other tests' rows. Assert membership of our own item
    # instead of exclusive table ownership -- same discipline as
    # test_rc34_job_queue_api_contract.py.
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)

        enqueue_response = scoped_client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc68-user",
                "title": "RC68 API",
                "message": "Outbox enqueue",
                "payload": {"source": "rc68"},
            },
            headers=internal_service_headers(),
        )

        assert enqueue_response.status_code == 200
        queued = enqueue_response.json()
        assert queued["status"] == "PENDING"

        pending_response = scoped_client.get(
            "/api/v1/notification-outbox/pending?limit=200", headers=headers
        )

        assert pending_response.status_code == 200
        pending = pending_response.json()

        pending_ids = [item["id"] for item in pending["items"]]
        assert queued["id"] in pending_ids


def test_rc68_outbox_claim_and_mark_delivered_api_contract():
    # Shared/persistent DB with many concurrent test workers, all racing on
    # the same global FIFO claim-next() pool -- there is no way to force
    # OUR item to be the one claimed next (no per-item reservation), so
    # trying to drain-until-found here is inherently contention-prone under
    # `pytest -n auto` (observed flaky: the whole suite's drain-loop tests
    # compete for the same backlog). The exact "claim-next() moves the just-
    # enqueued item PENDING->PROCESSING" mechanics are already covered
    # deterministically (isolated in-memory repo) by
    # test_rc68_notification_outbox_worker_service.py. This test instead
    # verifies claim-next()'s HTTP contract generically (valid response
    # shape) and mark-delivered's real lifecycle on OUR OWN item directly
    # -- mark_delivered() has no PROCESSING precondition, so it doesn't
    # need to be the one actually claimed.
    with TestClient(app) as scoped_client:
        queued = scoped_client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc68-user",
                "title": "RC68 API",
                "message": "Claim delivered",
            },
            headers=internal_service_headers(),
        ).json()

        claim_response = scoped_client.post(
            "/api/v1/notification-outbox/claim-next",
            json={"worker_id": "worker-rc68-api"},
            headers=internal_service_headers(),
        )
        assert claim_response.status_code == 200
        claimed = claim_response.json()
        assert isinstance(claimed["claimed"], bool)
        if claimed["claimed"]:
            assert claimed["item"]["status"] == "PROCESSING"

        delivered_response = scoped_client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-delivered",
            headers=internal_service_headers(),
        )
        assert delivered_response.status_code == 200
        delivered = delivered_response.json()

        assert delivered["updated"] is True
        assert delivered["item"]["status"] == "DELIVERED"


def test_rc68_outbox_mark_failed_api_contract():
    # AUTH-003 Part 1 event-loop lesson: chained DB requests need a single
    # `with TestClient(app) as client:` scope on Windows+asyncpg, not a
    # module-level client mixed with a separately-scoped one.
    with TestClient(app) as client:
        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc68-user",
                "title": "RC68 API",
                "message": "Claim failed",
            },
            headers=internal_service_headers(),
        ).json()

        client.post(
            "/api/v1/notification-outbox/claim-next",
            json={"worker_id": "worker-rc68-api-fail"},
            headers=internal_service_headers(),
        )

        failed_response = client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
            json={"error": "PROVIDER_TIMEOUT"},
            headers=internal_service_headers(),
        )

    assert failed_response.status_code == 200
    failed = failed_response.json()

    assert failed["updated"] is True
    assert failed["item"]["status"] == "FAILED"
    assert failed["item"]["last_error"] == "PROVIDER_TIMEOUT"
