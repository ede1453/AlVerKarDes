from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc89_instance_status_api_contract():
    response = client.get(
        "/api/v1/notification-outbox/scaling/instances/status"
    )

    assert response.status_code == 200
    data = response.json()

    assert "instance_count" in data
    assert "healthy_instance_count" in data
    assert "total_capacity" in data


def test_rc89_register_assign_release_instance_api_contract():
    register = client.post(
        "/api/v1/notification-outbox/scaling/instances",
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
        json={"request_id": "request-contract-1"},
    )

    assert assigned.status_code == 200
    assert assigned.json()["assigned"] is True

    instance_id = assigned.json()["instance"]["instance_id"]

    released = client.post(
        f"/api/v1/notification-outbox/scaling/instances/{instance_id}/release",
        json={"request_id": "request-contract-1"},
    )

    assert released.status_code == 200
    assert released.json()["released"] is True
