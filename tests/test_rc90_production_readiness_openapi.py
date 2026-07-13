from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc90_readiness_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/readiness/status" in paths
    assert "/api/v1/notification-outbox/readiness/checks" in paths

    assert "get" in paths[
        "/api/v1/notification-outbox/readiness/status"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/readiness/checks"
    ]
