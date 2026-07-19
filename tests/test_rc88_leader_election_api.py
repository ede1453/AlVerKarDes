from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def test_rc88_leader_status_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get(
            "/api/v1/notification-outbox/leader/status", headers=headers
        )

    assert response.status_code == 200
    data = response.json()

    assert "leader_id" in data
    assert "has_leader" in data


def test_rc88_acquire_renew_release_leadership_api_contract():
    with TestClient(app) as client:
        acquire = client.post(
            "/api/v1/notification-outbox/leader/acquire",
            headers=internal_service_headers(),
            json={
                "worker_id": "worker-api-1",
                "lease_seconds": 30,
            },
        )

        assert acquire.status_code == 200
        assert acquire.json()["acquired"] is True

        renew = client.post(
            "/api/v1/notification-outbox/leader/renew",
            headers=internal_service_headers(),
            json={
                "worker_id": "worker-api-1",
                "lease_seconds": 60,
            },
        )

        assert renew.status_code == 200
        assert renew.json()["renewed"] is True

        release = client.post(
            "/api/v1/notification-outbox/leader/release",
            headers=internal_service_headers(),
            json={
                "worker_id": "worker-api-1",
            },
        )

    assert release.status_code == 200
    assert release.json()["released"] is True
