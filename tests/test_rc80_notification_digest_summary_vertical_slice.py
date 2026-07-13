from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc80_vertical_slice_digest_only_pending_user_items():
    client.post("/api/v1/notification-outbox/clear")

    pending = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc80-user",
            "title": "Pending",
            "message": "Digest pending",
            "payload": {"source": "rc80"},
        },
    ).json()

    delivered = client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc80-user",
            "title": "Delivered",
            "message": "Should not be in digest",
            "payload": {"source": "rc80"},
        },
    ).json()

    client.post("/api/v1/notification-outbox/claim-next")
    client.post(f"/api/v1/notification-outbox/{pending['id']}/mark-delivered")

    digest = client.get("/api/v1/notification-outbox/digest/rc80-user").json()

    assert digest["item_count"] == 1
    assert digest["items"][0]["id"] == delivered["id"]
