
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc79_batch_delivery_api_contract():
    response = client.post(
        "/api/v1/notification-outbox/batch-summary",
        json={"notification_ids":["1","2","3"]}
    )
    assert response.status_code == 200
    assert response.json()["batch_size"] == 3
