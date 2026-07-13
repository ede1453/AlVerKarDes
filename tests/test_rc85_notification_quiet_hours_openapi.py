from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc85_openapi_contains_quiet_hours_endpoint():
    paths = client.get("/openapi.json").json()["paths"]

    path = "/api/v1/notification-outbox/quiet-hours/{user_id}"

    assert path in paths
    assert "get" in paths[path]
