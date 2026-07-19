from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

def test_rc211_rc215_vertical_slice():
    with TestClient(app) as client:
        headers = operator_headers(client)

        client.post(
            "/api/v1/deal-notification-operations/clear",
            headers=headers,
        )

        first = client.post(
            "/api/v1/deal-notification-operations/idempotency/reserve",
            headers=headers,
            json={
                "user_id":"u1",
                "deal_id":"d1",
                "channel":"push",
                "window_key":"2026-07-12"
            },
        ).json()

        second = client.post(
            "/api/v1/deal-notification-operations/idempotency/reserve",
            headers=headers,
            json={
                "user_id":"u1",
                "deal_id":"d1",
                "channel":"push",
                "window_key":"2026-07-12"
            },
        ).json()

        assert first["reserved"] is True
        assert second["reserved"] is False

        client.post(
            "/api/v1/deal-notification-operations/engagement",
            headers=headers,
            json={
                "notification_id":"n1",
                "user_id":"u1",
                "event_type":"DELIVERED",
                "channel":"push",
                "metadata":{}
            },
        )

        client.post(
            "/api/v1/deal-notification-operations/engagement",
            headers=headers,
            json={
                "notification_id":"n1",
                "user_id":"u1",
                "event_type":"OPENED",
                "channel":"push",
                "metadata":{}
            },
        )

        metrics = client.get(
            "/api/v1/deal-notification-operations/engagement/metrics",
            headers=headers,
            params={
                "user_id":"u1",
                "channel":"push"
            },
        ).json()

    assert metrics["open_rate"] == 1.0
