from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc71_dead_letter_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/dead-letters" in paths
    assert "/api/v1/notification-outbox/dead-letters/{item_id}/replay" in paths
    assert "get" in paths["/api/v1/notification-outbox/dead-letters"]
    assert "post" in paths["/api/v1/notification-outbox/dead-letters/{item_id}/replay"]
