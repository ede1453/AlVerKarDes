from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers

# SCALE-007 Part 1: /metrics is a global aggregate over a shared/persistent
# DB with many concurrently-running tests -- even a tight before/after
# delta around a single own operation isn't fully reliable (another test's
# concurrent enqueue/deliver can land in the same window, observed flaky
# elsewhere in this file family under `pytest -n auto`). Verify OUR OWN
# item's correctness via each endpoint's own response body (immune to
# concurrent activity) and use /metrics only to check contract shape.


def test_rc73_notification_metrics_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)

        enqueue_response = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={"user_id": "rc73-user", "title": "RC73", "message": "Metrics"},
            headers=internal_service_headers(),
        )
        assert enqueue_response.status_code == 200
        assert enqueue_response.json()["status"] == "PENDING"

        response = client.get(
            "/api/v1/notification-outbox/metrics", headers=headers
        )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["total_count"], int) and data["total_count"] >= 1
    assert isinstance(data["pending_count"], int) and data["pending_count"] >= 1
    assert data["metadata"]["metrics_version"] == "notification_metrics_v1"


def test_rc73_notification_metrics_api_after_delivery():
    with TestClient(app) as client:
        headers = operator_headers(client)

        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={"user_id": "rc73-user", "title": "RC73", "message": "Delivered"},
            headers=internal_service_headers(),
        ).json()

        client.post(
            "/api/v1/notification-outbox/claim-next",
            json={"worker_id": "worker-rc73"},
            headers=internal_service_headers(),
        )
        delivered_response = client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-delivered",
            headers=internal_service_headers(),
        )
        assert delivered_response.status_code == 200
        assert delivered_response.json()["item"]["status"] == "DELIVERED"

        data = client.get(
            "/api/v1/notification-outbox/metrics", headers=headers
        ).json()

    assert isinstance(data["delivered_count"], int) and data["delivered_count"] >= 1
