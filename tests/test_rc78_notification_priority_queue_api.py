
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc78_priority_queue_api_contract():
    response = client.get("/api/v1/notification-outbox/priority-queue/URGENT")
    assert response.status_code == 200
    assert response.json()["priority"] == "URGENT"
