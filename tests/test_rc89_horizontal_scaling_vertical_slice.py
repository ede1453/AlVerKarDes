from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def test_rc89_vertical_slice_register_balance_release():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post(
            "/api/v1/notification-outbox/scaling/instances",
            headers=internal_service_headers(),
            json={
                "instance_id": "api-v1",
                "capacity": 2,
                "healthy": True,
            },
        )
        client.post(
            "/api/v1/notification-outbox/scaling/instances",
            headers=internal_service_headers(),
            json={
                "instance_id": "api-v2",
                "capacity": 2,
                "healthy": True,
            },
        )

        first = client.post(
            "/api/v1/notification-outbox/scaling/assign",
            headers=internal_service_headers(),
            json={"request_id": "request-v1"},
        ).json()

        second = client.post(
            "/api/v1/notification-outbox/scaling/assign",
            headers=internal_service_headers(),
            json={"request_id": "request-v2"},
        ).json()

        assert first["assigned"] is True
        assert second["assigned"] is True
        assert first["instance"]["instance_id"] != second["instance"]["instance_id"]

        released = client.post(
            f"/api/v1/notification-outbox/scaling/instances/{first['instance']['instance_id']}/release",
            headers=internal_service_headers(),
            json={"request_id": "request-v1"},
        ).json()

        assert released["released"] is True

        status = client.get(
            "/api/v1/notification-outbox/scaling/instances/status",
            headers=headers,
        ).json()

    assert status["instance_count"] >= 2
    assert status["healthy_instance_count"] >= 2
