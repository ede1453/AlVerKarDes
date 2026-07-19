from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def test_rc71_vertical_slice_fail_to_dead_letter_then_replay_and_claim():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)

        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={
                "user_id": "rc71-user",
                "title": "RC71 vertical",
                "message": "DLQ replay",
                "payload": {"idempotency_key": "rc71-user:vertical"},
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

        dead_letters = client.get(
            "/api/v1/notification-outbox/dead-letters", headers=headers
        ).json()
        assert dead_letters["dead_letter_count"] == 1

        replayed = client.post(
            f"/api/v1/notification-outbox/dead-letters/{queued['id']}/replay",
            headers=headers,
        ).json()
        assert replayed["item"]["status"] == "PENDING"

        claimed = client.post(
            "/api/v1/notification-outbox/claim-next",
            headers=internal_service_headers(),
        ).json()
        assert claimed["claimed"] is True
        assert claimed["item"]["id"] == queued["id"]
