from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc75_circuit_breaker_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notification-outbox/circuit-breaker/status" in paths
    assert "/api/v1/notification-outbox/circuit-breaker/can-deliver" in paths
    assert "get" in paths["/api/v1/notification-outbox/circuit-breaker/status"]
    assert "get" in paths["/api/v1/notification-outbox/circuit-breaker/can-deliver"]
