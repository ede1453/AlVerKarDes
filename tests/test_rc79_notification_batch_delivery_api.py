
from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

def test_rc79_batch_delivery_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/notification-outbox/batch-summary",
            headers=headers,
            json={"notification_ids":["1","2","3"]}
        )
    assert response.status_code == 200
    assert response.json()["batch_size"] == 3
