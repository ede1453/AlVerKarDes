from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc88_leader_status_api_contract():
    response = client.get(
        "/api/v1/notification-outbox/leader/status"
    )

    assert response.status_code == 200
    data = response.json()

    assert "leader_id" in data
    assert "has_leader" in data


def test_rc88_acquire_renew_release_leadership_api_contract():
    acquire = client.post(
        "/api/v1/notification-outbox/leader/acquire",
        json={
            "worker_id": "worker-api-1",
            "lease_seconds": 30,
        },
    )

    assert acquire.status_code == 200
    assert acquire.json()["acquired"] is True

    renew = client.post(
        "/api/v1/notification-outbox/leader/renew",
        json={
            "worker_id": "worker-api-1",
            "lease_seconds": 60,
        },
    )

    assert renew.status_code == 200
    assert renew.json()["renewed"] is True

    release = client.post(
        "/api/v1/notification-outbox/leader/release",
        json={
            "worker_id": "worker-api-1",
        },
    )

    assert release.status_code == 200
    assert release.json()["released"] is True
