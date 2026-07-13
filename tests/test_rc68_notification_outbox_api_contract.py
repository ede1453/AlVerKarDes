from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc68_outbox_enqueue_and_pending_api_contract():
    client.post("/api/v1/notification-outbox/clear")

    enqueue_response = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc68-user",
            "title": "RC68 API",
            "message": "Outbox enqueue",
            "payload": {"source": "rc68"},
        },
    )

    assert enqueue_response.status_code == 200
    queued = enqueue_response.json()
    assert queued["status"] == "PENDING"

    pending_response = client.get("/api/v1/notification-outbox/pending")
    assert pending_response.status_code == 200
    pending = pending_response.json()

    assert pending["pending_count"] == 1
    assert pending["items"][0]["id"] == queued["id"]


def test_rc68_outbox_claim_and_mark_delivered_api_contract():
    client.post("/api/v1/notification-outbox/clear")
    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc68-user",
            "title": "RC68 API",
            "message": "Claim delivered",
        },
    ).json()

    claim_response = client.post("/api/v1/notification-outbox/claim-next")
    assert claim_response.status_code == 200
    claimed = claim_response.json()

    assert claimed["claimed"] is True
    assert claimed["item"]["id"] == queued["id"]
    assert claimed["item"]["status"] == "PROCESSING"

    delivered_response = client.post(
        f"/api/v1/notification-outbox/{queued['id']}/mark-delivered"
    )
    assert delivered_response.status_code == 200
    delivered = delivered_response.json()

    assert delivered["updated"] is True
    assert delivered["item"]["status"] == "DELIVERED"


def test_rc68_outbox_mark_failed_api_contract():
    client.post("/api/v1/notification-outbox/clear")
    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc68-user",
            "title": "RC68 API",
            "message": "Claim failed",
        },
    ).json()

    client.post("/api/v1/notification-outbox/claim-next")

    failed_response = client.post(
        f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
        json={"error": "PROVIDER_TIMEOUT"},
    )

    assert failed_response.status_code == 200
    failed = failed_response.json()

    assert failed["updated"] is True
    assert failed["item"]["status"] == "FAILED"
    assert failed["item"]["last_error"] == "PROVIDER_TIMEOUT"
