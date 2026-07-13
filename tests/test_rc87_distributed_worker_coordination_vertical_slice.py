from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc87_vertical_slice_register_assign_complete():
    client.post(
        "/api/v1/notification-outbox/workers",
        json={"worker_id": "worker-v1", "capacity": 1, "enabled": True},
    )
    assigned = client.post(
        "/api/v1/notification-outbox/workers/assign",
        json={"job_id": "job-v1"},
    ).json()
    assert assigned["assigned"] is True
    completed = client.post(
        f"/api/v1/notification-outbox/workers/{assigned['worker']['worker_id']}/complete",
        json={"job_id": "job-v1"},
    ).json()
    assert completed["completed"] is True
