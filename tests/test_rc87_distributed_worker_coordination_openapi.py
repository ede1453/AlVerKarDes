from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc87_worker_routes_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/notification-outbox/workers/status" in paths
    assert "/api/v1/notification-outbox/workers" in paths
    assert "/api/v1/notification-outbox/workers/assign" in paths
    assert "/api/v1/notification-outbox/workers/{worker_id}/complete" in paths
