from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_rc86_vertical_slice_register_status_run_status():
    with TestClient(app) as client:
        headers = operator_headers(client)
        register = client.post(
            "/api/v1/notification-outbox/scheduler/jobs",
            headers=headers,
            json={
                "job_name": "notification-retry-scheduler",
                "interval_seconds": 60,
                "enabled": True,
            },
        ).json()

        assert register["registered"] is True

        before = client.get(
            "/api/v1/notification-outbox/scheduler/status", headers=headers
        ).json()

        assert before["status"] == "RUNNING"
        assert before["job_count"] >= 1

        executed = client.post(
            "/api/v1/notification-outbox/scheduler/jobs/notification-retry-scheduler/run",
            headers=headers,
        ).json()

        assert executed["executed"] is True
        assert executed["job"]["run_count"] >= 1

        after = client.get(
            "/api/v1/notification-outbox/scheduler/status", headers=headers
        ).json()

    matching = [
        job
        for job in after["jobs"]
        if job["job_name"] == "notification-retry-scheduler"
    ]

    assert matching
    assert matching[0]["last_run_at"] is not None
