from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc85_vertical_slice_block_then_allow():
    blocked = client.get(
        "/api/v1/notification-outbox/quiet-hours/rc85-user",
        params={
            "current_hour": 2,
            "start_hour": 22,
            "end_hour": 8,
            "enabled": True,
        },
    ).json()

    allowed = client.get(
        "/api/v1/notification-outbox/quiet-hours/rc85-user",
        params={
            "current_hour": 10,
            "start_hour": 22,
            "end_hour": 8,
            "enabled": True,
        },
    ).json()

    assert blocked["allowed"] is False
    assert blocked["reason"] == "QUIET_HOURS_ACTIVE"
    assert allowed["allowed"] is True
    assert allowed["reason"] == "OUTSIDE_QUIET_HOURS"
