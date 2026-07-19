from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_rc86_scheduler_status_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get(
            "/api/v1/notification-outbox/scheduler/status", headers=headers
        )

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "job_count" in data
    assert data["metadata"]["scheduler_version"] == "background_job_scheduler_v1"


def test_rc86_scheduler_register_and_run_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        register_response = client.post(
            "/api/v1/notification-outbox/scheduler/jobs",
            headers=headers,
            json={
                "job_name": "notification-retry-scheduler",
                "interval_seconds": 60,
                "enabled": True,
            },
        )

        assert register_response.status_code == 200
        assert register_response.json()["registered"] is True

        run_response = client.post(
            "/api/v1/notification-outbox/scheduler/jobs/notification-retry-scheduler/run",
            headers=headers,
        )

    assert run_response.status_code == 200
    assert run_response.json()["executed"] is True
