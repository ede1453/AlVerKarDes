
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc76_openapi_route_exists():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/notification-outbox/rate-limit/{user_id}" in paths
