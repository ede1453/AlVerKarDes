from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_provider_scheduler_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/provider-schedules" in paths
    assert "/api/v1/provider-schedules/{schedule_id}" in paths
    assert "/api/v1/provider-schedules/{schedule_id}/run-once" in paths
    assert "/api/v1/api/v1/provider-schedules" not in paths
