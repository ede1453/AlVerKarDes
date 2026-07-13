from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc68_notification_outbox_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    expected_paths = {
        "/api/v1/notification-outbox/enqueue",
        "/api/v1/notification-outbox/enqueue-many",
        "/api/v1/notification-outbox/pending",
        "/api/v1/notification-outbox/claim-next",
        "/api/v1/notification-outbox/{item_id}/mark-delivered",
        "/api/v1/notification-outbox/{item_id}/mark-failed",
        "/api/v1/notification-outbox/clear",
    }

    for path in expected_paths:
        assert path in paths
