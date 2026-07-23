from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id, internal_service_headers


def test_rc80_digest_summary_api_contract():
    # SCALE-007 Part 1: no /clear (shared/persistent DB, would disrupt
    # other parallel tests) -- unnecessary here anyway, since digest is
    # scoped to this test's own freshly-registered (unique) user_id.
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post(
            "/api/v1/notification-outbox/enqueue",
            headers={**internal_service_headers(), **headers},
            json={
                "user_id": user_id,
                "title": "RC80",
                "message": "Digest item",
                "payload": {"source": "rc80"},
            },
        )

        response = client.get(
            f"/api/v1/notification-outbox/digest/{user_id}", headers=headers
        )

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == user_id
    assert data["item_count"] == 1
    assert data["metadata"]["digest_version"] == "notification_digest_v1"
