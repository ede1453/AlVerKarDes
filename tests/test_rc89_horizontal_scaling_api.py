from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers

client = TestClient(app)


def test_rc89_instance_status_api_contract():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        response = scoped_client.get(
            "/api/v1/notification-outbox/scaling/instances/status",
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()

    assert "instance_count" in data
    assert "healthy_instance_count" in data
    assert "total_capacity" in data


def test_rc89_register_assign_release_instance_api_contract():
    register = client.post(
        "/api/v1/notification-outbox/scaling/instances",
        headers=internal_service_headers(),
        json={
            "instance_id": "api-contract-1",
            "capacity": 2,
            "healthy": True,
        },
    )

    assert register.status_code == 200
    assert register.json()["registered"] is True

    assigned = client.post(
        "/api/v1/notification-outbox/scaling/assign",
        headers=internal_service_headers(),
        json={"request_id": "request-contract-1"},
    )

    assert assigned.status_code == 200
    assert assigned.json()["assigned"] is True

    instance_id = assigned.json()["instance"]["instance_id"]

    released = client.post(
        f"/api/v1/notification-outbox/scaling/instances/{instance_id}/release",
        headers=internal_service_headers(),
        json={"request_id": "request-contract-1"},
    )

    assert released.status_code == 200
    assert released.json()["released"] is True
