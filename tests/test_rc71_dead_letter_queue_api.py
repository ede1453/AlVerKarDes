from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def _create_dead_letter_item(client):
    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc71-user",
            "title": "RC71 API",
            "message": "Dead letter",
            "payload": {"source": "rc71"},
        },
        headers=internal_service_headers(),
    ).json()

    for _ in range(3):
        client.post(
            "/api/v1/notification-outbox/claim-next",
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
                "/api/v1/notification-outbox/requeue-due-retries",
                headers=internal_service_headers(),
            )

    return queued


def test_rc71_dead_letter_list_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)
        queued = _create_dead_letter_item(client)

        response = client.get(
            "/api/v1/notification-outbox/dead-letters", headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["dead_letter_count"] == 1
        assert data["items"][0]["id"] == queued["id"]
        assert data["items"][0]["status"] == "DEAD_LETTER"


def test_rc71_dead_letter_replay_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)
        queued = _create_dead_letter_item(client)

        response = client.post(
            f"/api/v1/notification-outbox/dead-letters/{queued['id']}/replay",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["replayed"] is True
        assert data["item"]["status"] == "PENDING"
