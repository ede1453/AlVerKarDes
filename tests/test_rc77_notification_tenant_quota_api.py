
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc77_tenant_quota_api_contract():
    response = client.get("/api/v1/notification-outbox/tenant-quota/tenant-a")
    assert response.status_code == 200
    assert "allowed" in response.json()
