
from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

def test_rc77_tenant_quota_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get(
            "/api/v1/notification-outbox/tenant-quota/tenant-a", headers=headers
        )
    assert response.status_code == 200
    assert "allowed" in response.json()
