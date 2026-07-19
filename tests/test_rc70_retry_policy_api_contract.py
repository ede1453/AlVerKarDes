from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)


def test_rc70_mark_failed_api_calculates_backoff_when_next_retry_at_missing():
    client.post("/api/v1/notification-outbox/clear")

    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc70-user",
            "title": "RC70 API",
            "message": "Backoff API",
            "payload": {"source": "rc70"},
        },
        headers=internal_service_headers(),
    ).json()

    client.post(
        "/api/v1/notification-outbox/claim-next",
        headers=internal_service_headers(),
    )

    response = client.post(
        f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
        json={"error": "PROVIDER_TIMEOUT"},
        headers=internal_service_headers(),
    )

    assert response.status_code == 200
    data = response.json()

    assert data["updated"] is True
    assert data["item"]["status"] == "FAILED"
    assert data["item"]["retry_count"] == 1
    assert data["item"]["next_retry_at"] is not None


def test_rc70_mark_failed_api_preserves_explicit_next_retry_at():
    client.post("/api/v1/notification-outbox/clear")

    queued = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc70-user",
            "title": "RC70 API",
            "message": "Explicit next retry",
        },
        headers=internal_service_headers(),
    ).json()

    client.post(
        "/api/v1/notification-outbox/claim-next",
        headers=internal_service_headers(),
    )

    response = client.post(
        f"/api/v1/notification-outbox/{queued['id']}/mark-failed",
        json={
            "error": "PROVIDER_TIMEOUT",
            "next_retry_at": "2000-01-01T00:00:00+00:00",
        },
        headers=internal_service_headers(),
    )

    assert response.status_code == 200
    assert response.json()["item"]["next_retry_at"] == "2000-01-01T00:00:00+00:00"
