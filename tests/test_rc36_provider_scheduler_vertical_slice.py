from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)


def test_provider_scheduler_vertical_slice_emits_event_after_health_check():
    client.post("/api/v1/events/clear", headers=internal_service_headers())

    schedule_response = client.post(
        "/api/v1/provider-schedules",
        json={
            "name": "health-check",
            "providers": ["mock", "openai"],
            "interval_seconds": 60,
        },
        headers=internal_service_headers(),
    )
    assert schedule_response.status_code == 200
    schedule = schedule_response.json()

    run_response = client.post(
        f"/api/v1/provider-schedules/{schedule['id']}/run-once",
        headers=internal_service_headers(),
    )
    assert run_response.status_code == 200

    event_response = client.get(
        "/api/v1/events?event_type=provider_health.checked&source=provider_scheduler",
        headers=internal_service_headers(),
    )
    assert event_response.status_code == 200
    assert event_response.json()["items"]
