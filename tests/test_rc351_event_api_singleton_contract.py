from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)


def test_event_api_publish_then_list_uses_same_repository():
    client.post("/api/v1/events/clear", headers=internal_service_headers())

    event_response = client.post(
        "/api/v1/events/publish",
        json={
            "event_type": "api.singleton.test",
            "source": "test",
            "payload": {"ok": True},
        },
        headers=internal_service_headers(),
    )

    assert event_response.status_code == 200
    event = event_response.json()

    list_response = client.get(
        "/api/v1/events?event_type=api.singleton.test&source=test",
        headers=internal_service_headers(),
    )

    assert list_response.status_code == 200
    assert any(item["id"] == event["id"] for item in list_response.json()["items"])


def test_event_status_exposes_singleton_lifecycle():
    response = client.get("/api/v1/events/status", headers=internal_service_headers())

    assert response.status_code == 200
    assert response.json()["repository_lifecycle"] == "singleton"
