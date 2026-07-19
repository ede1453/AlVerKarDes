from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_rc85_vertical_slice_block_then_allow():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        blocked = client.get(
            f"/api/v1/notification-outbox/quiet-hours/{user_id}",
            headers=headers,
            params={
                "current_hour": 2,
                "start_hour": 22,
                "end_hour": 8,
                "enabled": True,
            },
        ).json()

        allowed = client.get(
            f"/api/v1/notification-outbox/quiet-hours/{user_id}",
            headers=headers,
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
