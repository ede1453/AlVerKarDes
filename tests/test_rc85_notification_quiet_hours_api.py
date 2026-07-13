from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc85_quiet_hours_api_contract():
    response = client.get(
        "/api/v1/notification-outbox/quiet-hours/rc85-user",
        params={
            "current_hour": 23,
            "start_hour": 22,
            "end_hour": 8,
            "enabled": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "rc85-user"
    assert data["allowed"] is False
    assert data["quiet_hours_active"] is True
    assert data["metadata"]["quiet_hours_version"] == "notification_quiet_hours_v1"
