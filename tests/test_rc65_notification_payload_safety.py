from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_rc65_notification_response_does_not_leak_provider_secrets(monkeypatch):
    monkeypatch.setenv("NOTIFICATION_PROVIDER_API_KEY", "super-secret-provider-key")

    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        response = client.post(
            "/api/v1/notifications/deliver",
            headers=headers,
            json={
                "user_id": user_id,
                "channels": ["in_app"],
                "title": "Secret leak check",
                "message": "Provider secret must not appear.",
                "payload": {"source": "rc65"},
            },
        )

    assert response.status_code == 200
    text = str(response.json())

    assert "super-secret-provider-key" not in text
    assert "NOTIFICATION_PROVIDER_API_KEY" not in text
