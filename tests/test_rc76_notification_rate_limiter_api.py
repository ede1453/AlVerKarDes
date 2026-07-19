
from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id

def test_rc76_rate_limit_api_contract():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        response = client.get(
            f"/api/v1/notification-outbox/rate-limit/{user_id}", headers=headers
        )
    assert response.status_code == 200
    assert "allowed" in response.json()
