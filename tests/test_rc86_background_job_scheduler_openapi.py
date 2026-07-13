from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc86_scheduler_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/scheduler/status" in paths
    assert "/api/v1/notification-outbox/scheduler/jobs" in paths
    assert (
        "/api/v1/notification-outbox/scheduler/jobs/{job_name}/run"
        in paths
    )

    assert "get" in paths[
        "/api/v1/notification-outbox/scheduler/status"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/scheduler/jobs"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/scheduler/jobs/{job_name}/run"
    ]
