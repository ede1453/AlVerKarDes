from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def test_rc73_vertical_slice_metrics_across_lifecycle():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)

        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            headers=internal_service_headers(),
            json={
                "user_id": "rc73-user",
                "title": "RC73 vertical",
                "message": "Metrics lifecycle",
            },
        ).json()

        initial = client.get(
            "/api/v1/notification-outbox/metrics", headers=headers
        ).json()
        assert initial["pending_count"] == 1

        client.post(
            "/api/v1/notification-outbox/claim-next",
            headers=internal_service_headers(),
        )
        processing = client.get(
            "/api/v1/notification-outbox/metrics", headers=headers
        ).json()
        assert processing["processing_count"] == 1

        client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-delivered",
            headers=internal_service_headers(),
        )
        delivered = client.get(
            "/api/v1/notification-outbox/metrics", headers=headers
        ).json()

    assert delivered["delivered_count"] == 1
    assert delivered["delivery_success_rate"] == 1.0
