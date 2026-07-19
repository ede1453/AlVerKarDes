from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

def test_rc216_rc220_vertical_slice():
    with TestClient(app) as client:
        headers = operator_headers(client)

        client.post(
            "/api/v1/deal-notification-providers/clear",
            headers=headers,
        )

        registered = client.post(
            "/api/v1/deal-notification-providers/providers",
            headers=headers,
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
            headers=headers,
            params={"channel":"push"},
        ).json()

        assert selected["provider"]["provider_id"] == "push-primary"

        client.post(
            "/api/v1/deal-notification-providers/subscriptions",
            headers=headers,
            json={
                "user_id":"u1",
                "channel":"email",
                "subscribed":False,
                "source":"user_request"
            },
        )

        status = client.get(
            "/api/v1/deal-notification-providers/subscriptions/unsubscribed",
            headers=headers,
            params={
                "user_id":"u1",
                "channel":"email"
            },
        ).json()

    assert status["unsubscribed"] is True
