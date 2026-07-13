from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc93_release_promotion_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/release-promotion/status" in paths
    assert "/api/v1/notification-outbox/release-promotion/promote" in paths

    assert "get" in paths[
        "/api/v1/notification-outbox/release-promotion/status"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/release-promotion/promote"
    ]
