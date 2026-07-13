from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc211_rc215_vertical_slice():
    client.post(
        "/api/v1/deal-notification-operations/clear"
    )

    first = client.post(
        "/api/v1/deal-notification-operations/idempotency/reserve",
        json={
            "user_id":"u1",
            "deal_id":"d1",
            "channel":"push",
            "window_key":"2026-07-12"
        },
    ).json()

    second = client.post(
        "/api/v1/deal-notification-operations/idempotency/reserve",
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
        params={
            "user_id":"u1",
            "channel":"push"
        },
    ).json()

    assert metrics["open_rate"] == 1.0
