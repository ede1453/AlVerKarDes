from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def _make_dead_letter_via_api(client) -> dict:
    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc72-user",
            "title": "RC72 API",
            "message": "DLQ replay audit",
            "payload": {"source": "rc72"},
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


def test_rc72_replay_dead_letter_api_accepts_audit_payload():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)
        queued = _make_dead_letter_via_api(client)

        response = client.post(
            f"/api/v1/notification-outbox/dead-letters/{queued['id']}/replay",
            headers=headers,
            json={
                "replay_reason": "manual_admin_retry",
                "replayed_by": "rc72-admin",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["replayed"] is True
        assert data["item"]["status"] == "PENDING"
        assert data["item"]["payload"]["dlq_replay"]["reason"] == "manual_admin_retry"
        assert data["item"]["payload"]["dlq_replay"]["replayed_by"] == "rc72-admin"
