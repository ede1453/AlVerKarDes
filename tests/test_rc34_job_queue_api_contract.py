from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)


def test_job_queue_api_enqueue_and_get():
    response = client.post(
        "/api/v1/jobs/enqueue",
        json={
            "job_type": "noop",
            "payload": {"x": 1},
        },
        headers=internal_service_headers(),
    )

    assert response.status_code == 200
    job = response.json()

    get_response = client.get(f"/api/v1/jobs/{job['id']}", headers=internal_service_headers())

    assert get_response.status_code == 200
    assert get_response.json()["id"] == job["id"]


def test_job_queue_api_run_now():
    response = client.post(
        "/api/v1/jobs/run-now",
        json={
            "job_type": "noop",
            "payload": {"x": 1},
        },
        headers=internal_service_headers(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
