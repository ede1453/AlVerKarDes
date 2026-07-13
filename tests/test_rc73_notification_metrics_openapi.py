from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc73_notification_metrics_route_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/metrics" in paths
    assert "get" in paths["/api/v1/notification-outbox/metrics"]
