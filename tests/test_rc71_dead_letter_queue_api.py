from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers

# SCALE-007 Part 1: shared/persistent DB -- no /clear (would disrupt other
# parallel tests), assertions check membership/own-item shape instead of
# exclusive-table-state counts (same discipline as
# test_rc34_job_queue_api_contract.py).


def _create_dead_letter_item(client, worker_id):
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
            json={"worker_id": worker_id},
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

    return queued


def test_rc71_dead_letter_list_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        queued = _create_dead_letter_item(client, "worker-rc71-list")

        response = client.get(
            "/api/v1/notification-outbox/dead-letters?limit=200", headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        dead_letters_by_id = {item["id"]: item for item in data["items"]}
        assert queued["id"] in dead_letters_by_id
        assert dead_letters_by_id[queued["id"]]["status"] == "DEAD_LETTER"


def test_rc71_dead_letter_replay_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        queued = _create_dead_letter_item(client, "worker-rc71-replay")

        response = client.post(
            f"/api/v1/notification-outbox/dead-letters/{queued['id']}/replay",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["replayed"] is True
        assert data["item"]["status"] == "PENDING"
