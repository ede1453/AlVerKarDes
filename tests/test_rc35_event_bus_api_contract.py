from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_event_bus_api_publish_and_list():
    assert client.post("/api/v1/events/clear").status_code == 200

    response = client.post(
        "/api/v1/events/publish",
        json={
            "event_type": "job.completed",
            "source": "jobs",
            "payload": {"job_id": "job-1"},
        },
    )

    assert response.status_code == 200
    event = response.json()

    list_response = client.get("/api/v1/events?limit=10&source=jobs")

    assert list_response.status_code == 200
    assert any(item["id"] == event["id"] for item in list_response.json()["items"])


def test_event_bus_status_api():
    response = client.get("/api/v1/events/status")

    assert response.status_code == 200
    assert response.json()["enabled"] is True
