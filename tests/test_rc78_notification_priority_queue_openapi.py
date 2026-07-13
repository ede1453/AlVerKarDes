
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc78_openapi_contains_priority_queue_endpoint():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/notification-outbox/priority-queue/{priority}" in paths
