from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc216_rc220_vertical_slice():
    client.post(
        "/api/v1/deal-notification-providers/clear"
    )

    registered = client.post(
        "/api/v1/deal-notification-providers/providers",
        json={
            "provider_id":"push-primary",
            "channel":"push",
            "priority":10,
            "enabled":True,
            "metadata":{}
        },
    ).json()

    assert registered["registered"] is True

    selected = client.get(
        "/api/v1/deal-notification-providers/providers/select",
        params={"channel":"push"},
    ).json()

    assert selected["provider"]["provider_id"] == "push-primary"

    client.post(
        "/api/v1/deal-notification-providers/subscriptions",
        json={
            "user_id":"u1",
            "channel":"email",
            "subscribed":False,
            "source":"user_request"
        },
    )

    status = client.get(
        "/api/v1/deal-notification-providers/subscriptions/unsubscribed",
        params={
            "user_id":"u1",
            "channel":"email"
        },
    ).json()

    assert status["unsubscribed"] is True
