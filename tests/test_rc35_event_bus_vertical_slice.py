from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)


def test_event_bus_vertical_slice_after_job_execution():
    client.post("/api/v1/events/clear", headers=internal_service_headers())

    job_response = client.post(
        "/api/v1/jobs/run-now",
        json={
            "job_type": "noop",
            "payload": {"source": "event-test"},
        },
        headers=internal_service_headers(),
    )

    assert job_response.status_code == 200
    job = job_response.json()

    event_response = client.post(
        "/api/v1/events/publish",
        json={
            "event_type": "job.completed",
            "source": "jobs",
            "payload": {
                "job_id": job["id"],
                "job_type": job["job_type"],
                "status": job["status"],
            },
            "metadata": {
                "event_version": "event_v1",
            },
        },
        headers=internal_service_headers(),
    )

    assert event_response.status_code == 200

    events_response = client.get(
        "/api/v1/events?event_type=job.completed&source=jobs",
        headers=internal_service_headers(),
    )

    assert events_response.status_code == 200
    assert any(item["payload"]["job_id"] == job["id"] for item in events_response.json()["items"])
