from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc80_openapi_contains_digest_endpoint():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/digest/{user_id}" in paths
    assert "get" in paths["/api/v1/notification-outbox/digest/{user_id}"]
