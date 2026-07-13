from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc86_scheduler_status_api_contract():
    response = client.get(
        "/api/v1/notification-outbox/scheduler/status"
    )

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "job_count" in data
    assert data["metadata"]["scheduler_version"] == "background_job_scheduler_v1"


def test_rc86_scheduler_register_and_run_api_contract():
    register_response = client.post(
        "/api/v1/notification-outbox/scheduler/jobs",
        json={
            "job_name": "notification-retry-scheduler",
            "interval_seconds": 60,
            "enabled": True,
        },
    )

    assert register_response.status_code == 200
    assert register_response.json()["registered"] is True

    run_response = client.post(
        "/api/v1/notification-outbox/scheduler/jobs/notification-retry-scheduler/run"
    )

    assert run_response.status_code == 200
    assert run_response.json()["executed"] is True
