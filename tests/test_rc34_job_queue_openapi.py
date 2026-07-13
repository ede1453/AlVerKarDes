from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_job_queue_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/jobs/enqueue" in paths
    assert "/api/v1/jobs/run-now" in paths
    assert "/api/v1/jobs" in paths
    assert "/api/v1/jobs/{job_id}" in paths
    assert "/api/v1/api/v1/jobs/enqueue" not in paths
