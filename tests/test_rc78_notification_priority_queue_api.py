
from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

def test_rc78_priority_queue_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get(
            "/api/v1/notification-outbox/priority-queue/URGENT", headers=headers
        )
    assert response.status_code == 200
    assert response.json()["priority"] == "URGENT"
