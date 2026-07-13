from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc89_horizontal_scaling_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/scaling/instances/status" in paths
    assert "/api/v1/notification-outbox/scaling/instances" in paths
    assert "/api/v1/notification-outbox/scaling/assign" in paths
    assert (
        "/api/v1/notification-outbox/scaling/instances/{instance_id}/release"
        in paths
    )

    assert "get" in paths[
        "/api/v1/notification-outbox/scaling/instances/status"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/scaling/instances"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/scaling/assign"
    ]
    assert "post" in paths[
        "/api/v1/notification-outbox/scaling/instances/{instance_id}/release"
    ]
