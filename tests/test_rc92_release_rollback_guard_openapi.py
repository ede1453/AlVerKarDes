from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc92_release_rollback_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/release-rollback/status" in paths
    assert "/api/v1/notification-outbox/release-rollback/request" in paths
    assert "/api/v1/notification-outbox/release-rollback/complete" in paths

    assert "get" in paths[
        "/api/v1/notification-outbox/release-rollback/status"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/release-rollback/request"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/release-rollback/complete"
    ]
