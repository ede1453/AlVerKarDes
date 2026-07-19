from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id, internal_service_headers


def test_rc80_vertical_slice_digest_only_pending_user_items():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post("/api/v1/notification-outbox/clear", headers=headers)

        pending = client.post(
            "/api/v1/notification-outbox/enqueue",
            headers={**internal_service_headers(), **headers},
            json={
                "user_id": user_id,
                "title": "Pending",
                "message": "Digest pending",
                "payload": {"source": "rc80"},
            },
        ).json()

        delivered = client.post(
            "/api/v1/notification-outbox/enqueue",
            headers={**internal_service_headers(), **headers},
            json={
                "user_id": user_id,
                "title": "Delivered",
                "message": "Should not be in digest",
                "payload": {"source": "rc80"},
            },
        ).json()

        client.post(
            "/api/v1/notification-outbox/claim-next",
            headers={**internal_service_headers(), **headers},
        )
        client.post(
            f"/api/v1/notification-outbox/{pending['id']}/mark-delivered",
            headers={**internal_service_headers(), **headers},
        )

        digest = client.get(
            f"/api/v1/notification-outbox/digest/{user_id}", headers=headers
        ).json()

    assert digest["item_count"] == 1
    assert digest["items"][0]["id"] == delivered["id"]
