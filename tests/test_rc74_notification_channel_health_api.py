from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc74_channel_health_endpoint_exists():
    response = client.get(
        "/api/v1/notification-outbox/channel-health"
    )

    assert response.status_code == 200