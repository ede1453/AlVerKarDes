from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_provider_scheduler_api_create_get_run_once():
    response = client.post(
        "/api/v1/provider-schedules",
        json={
            "name": "provider-health",
            "providers": ["mock"],
            "interval_seconds": 30,
        },
    )

    assert response.status_code == 200
    schedule = response.json()

    get_response = client.get(f"/api/v1/provider-schedules/{schedule['id']}")
    assert get_response.status_code == 200

    run_response = client.post(f"/api/v1/provider-schedules/{schedule['id']}/run-once")
    assert run_response.status_code == 200
    assert run_response.json()["result"]["status"] == "HEALTHY"


def test_provider_scheduler_api_list():
    response = client.get("/api/v1/provider-schedules")

    assert response.status_code == 200
    assert "items" in response.json()
