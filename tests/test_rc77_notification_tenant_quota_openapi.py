
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc77_openapi_contains_tenant_quota_endpoint():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/notification-outbox/tenant-quota/{tenant_id}" in paths
