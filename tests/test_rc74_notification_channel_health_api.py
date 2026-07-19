from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_rc74_channel_health_endpoint_exists():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get(
            "/api/v1/notification-outbox/channel-health", headers=headers
        )

    assert response.status_code == 200
