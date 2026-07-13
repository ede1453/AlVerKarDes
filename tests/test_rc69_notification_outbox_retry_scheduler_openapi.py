from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc69_requeue_due_retries_route_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/requeue-due-retries" in paths
    assert "post" in paths["/api/v1/notification-outbox/requeue-due-retries"]
