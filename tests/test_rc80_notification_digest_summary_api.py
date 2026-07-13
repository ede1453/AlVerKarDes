from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc80_digest_summary_api_contract():
    client.post("/api/v1/notification-outbox/clear")

    client.post(
        "/api/v1/notification-outbox/enqueue",
        json={
            "user_id": "rc80-user",
            "title": "RC80",
            "message": "Digest item",
            "payload": {"source": "rc80"},
        },
    )

    response = client.get("/api/v1/notification-outbox/digest/rc80-user")

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "rc80-user"
    assert data["item_count"] == 1
    assert data["metadata"]["digest_version"] == "notification_digest_v1"
