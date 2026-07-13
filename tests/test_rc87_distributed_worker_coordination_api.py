from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc87_worker_status_api_contract():
    response = client.get("/api/v1/notification-outbox/workers/status")
    assert response.status_code == 200
    assert "workers" in response.json()

def test_rc87_register_assign_complete_api_contract():
    register = client.post(
        "/api/v1/notification-outbox/workers",
        json={"worker_id": "worker-api-1", "capacity": 2, "enabled": True},
    )
    assert register.status_code == 200
    assigned = client.post(
        "/api/v1/notification-outbox/workers/assign",
        json={"job_id": "job-api-1"},
    )
    assert assigned.status_code == 200
    worker_id = assigned.json()["worker"]["worker_id"]
    completed = client.post(
        f"/api/v1/notification-outbox/workers/{worker_id}/complete",
        json={"job_id": "job-api-1"},
    )
    assert completed.status_code == 200
    assert completed.json()["completed"] is True
