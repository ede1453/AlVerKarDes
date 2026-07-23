from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id, internal_service_headers


def test_rc80_vertical_slice_digest_only_pending_user_items():
    # SCALE-007 Part 1: no /clear (shared/persistent DB) -- unnecessary
    # here anyway, digest is scoped to this test's own unique user_id.
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

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

        # mark_delivered() has no PROCESSING precondition -- no need to
        # claim-next() first. Skipping it also avoids risking our own
        # `delivered` item (which must stay PENDING) getting claimed by a
        # concurrently-running test's unrelated claim-next() call (shared/
        # persistent DB, SCALE-007 Part 1 -- claim-next has no per-item
        # reservation, it's a real global FIFO pool).
        client.post(
            f"/api/v1/notification-outbox/{pending['id']}/mark-delivered",
            headers={**internal_service_headers(), **headers},
        )

        digest = client.get(
            f"/api/v1/notification-outbox/digest/{user_id}", headers=headers
        ).json()

    assert digest["item_count"] == 1
    assert digest["items"][0]["id"] == delivered["id"]
