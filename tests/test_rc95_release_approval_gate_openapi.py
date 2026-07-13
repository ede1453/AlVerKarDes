from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc95_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/notification-outbox/release-approval/status" in paths
    assert "/api/v1/notification-outbox/release-approval/approve" in paths
    assert "/api/v1/notification-outbox/release-approval/revoke" in paths
