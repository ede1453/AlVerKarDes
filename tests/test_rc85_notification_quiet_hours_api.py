from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_rc85_quiet_hours_api_contract():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        response = client.get(
            f"/api/v1/notification-outbox/quiet-hours/{user_id}",
            headers=headers,
            params={
                "current_hour": 23,
                "start_hour": 22,
                "end_hour": 8,
                "enabled": True,
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == user_id
    assert data["allowed"] is False
    assert data["quiet_hours_active"] is True
    assert data["metadata"]["quiet_hours_version"] == "notification_quiet_hours_v1"
