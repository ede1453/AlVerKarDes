from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import (
    auth_headers,
    internal_service_headers,
    operator_headers,
)

client = TestClient(app)


def test_rc68_outbox_enqueue_and_pending_api_contract():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        scoped_client.post("/api/v1/notification-outbox/clear", headers=headers)

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
            "/api/v1/notification-outbox/pending", headers=headers
        )

        assert pending_response.status_code == 200
        pending = pending_response.json()

        assert pending["pending_count"] == 1
        assert pending["items"][0]["id"] == queued["id"]


def test_rc68_outbox_claim_and_mark_delivered_api_contract():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        scoped_client.post("/api/v1/notification-outbox/clear", headers=headers)
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
            headers=internal_service_headers(),
        )
        assert claim_response.status_code == 200
        claimed = claim_response.json()

        assert claimed["claimed"] is True
        assert claimed["item"]["id"] == queued["id"]
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
    with TestClient(app) as scoped_client:
        headers = auth_headers(scoped_client)
        scoped_client.post("/api/v1/notification-outbox/clear", headers=headers)
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
