from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc94_release_audit_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/release-audit/events" in paths
    assert "get" in paths[
        "/api/v1/notification-outbox/release-audit/events"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/release-audit/events"
    ]
