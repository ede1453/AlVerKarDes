from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc88_leader_election_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/leader/status" in paths
    assert "/api/v1/notification-outbox/leader/acquire" in paths
    assert "/api/v1/notification-outbox/leader/renew" in paths
    assert "/api/v1/notification-outbox/leader/release" in paths

    assert "get" in paths[
        "/api/v1/notification-outbox/leader/status"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/leader/acquire"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/leader/renew"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/leader/release"
    ]
