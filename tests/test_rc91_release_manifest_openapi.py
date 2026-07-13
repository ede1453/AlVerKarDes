from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc91_release_manifest_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/release-manifest" in paths
    assert "/api/v1/notification-outbox/release-manifest/publish" in paths

    assert "get" in paths[
        "/api/v1/notification-outbox/release-manifest"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/release-manifest/publish"
    ]
