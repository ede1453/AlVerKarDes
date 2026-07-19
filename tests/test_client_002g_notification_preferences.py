"""CLIENT-002g: deal-notification preferences (channels/thresholds/quiet
hours) moved from in-memory to Postgres (notification_preferences table,
migration 0019), same pattern as watchlist (CLIENT-002e). Ownership
guard (ensure_owner) already existed on these endpoints -- these tests
add the same two attack vectors CLIENT-002d/002e added for watchlist:
impersonation on write, cross-user read.
"""

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_real_preferences_write_then_read_roundtrip():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        set_response = client.post(
            "/api/v1/deal-notifications/preferences",
            headers=headers,
            json={
                "user_id": user_id,
                "enabled_channels": ["email", "push"],
                "minimum_confidence": 85,
                "minimum_discount_pct": 15,
                "quiet_hours_enabled": True,
                "quiet_hours_start": "23:00",
                "quiet_hours_end": "07:00",
            },
        )
        assert set_response.status_code == 200, set_response.text
        assert set_response.json()["preferences"]["enabled_channels"] == ["email", "push"]

        get_response = client.get(
            f"/api/v1/deal-notifications/preferences/{user_id}", headers=headers
        )

    assert get_response.status_code == 200
    body = get_response.json()
    assert body["enabled_channels"] == ["email", "push"]
    assert body["minimum_confidence"] == 85
    assert body["quiet_hours_enabled"] is True
    assert body["quiet_hours_start"] == "23:00"


def test_cannot_set_preferences_under_another_users_id():
    with TestClient(app) as client:
        headers_a, _user_a = auth_headers_and_user_id(client)
        headers_b, user_b = auth_headers_and_user_id(client)

        attempt = client.post(
            "/api/v1/deal-notifications/preferences",
            headers=headers_a,
            json={"user_id": user_b, "enabled_channels": ["email"]},
        )

    assert attempt.status_code == 403, attempt.text
    assert attempt.json()["detail"]["code"] == "NOT_RESOURCE_OWNER"


def test_cannot_read_another_users_preferences():
    with TestClient(app) as client:
        headers_a, user_a = auth_headers_and_user_id(client)
        headers_b, _user_b = auth_headers_and_user_id(client)

        client.post(
            "/api/v1/deal-notifications/preferences",
            headers=headers_a,
            json={"user_id": user_a, "enabled_channels": ["push"]},
        )

        cross_user_get = client.get(
            f"/api/v1/deal-notifications/preferences/{user_a}", headers=headers_b
        )
        own_get = client.get(
            f"/api/v1/deal-notifications/preferences/{user_a}", headers=headers_a
        )

    assert cross_user_get.status_code == 403, cross_user_get.text
    assert own_get.status_code == 200, own_get.text


def test_unset_user_gets_honest_defaults_not_a_crash():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        response = client.get(
            f"/api/v1/deal-notifications/preferences/{user_id}", headers=headers
        )

    assert response.status_code == 200
    body = response.json()
    assert body["enabled_channels"] == ["in_app"]
    assert body["minimum_confidence"] == 70.0
