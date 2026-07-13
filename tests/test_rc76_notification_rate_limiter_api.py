
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc76_rate_limit_api_contract():
    response = client.get("/api/v1/notification-outbox/rate-limit/user1")
    assert response.status_code == 200
    assert "allowed" in response.json()
