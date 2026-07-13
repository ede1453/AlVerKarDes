from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc74_channel_health_openapi_registered():
    schema = client.get("/openapi.json").json()

    assert (
        "/api/v1/notification-outbox/channel-health"
        in schema["paths"]
    )