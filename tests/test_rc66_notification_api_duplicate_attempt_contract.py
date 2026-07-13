from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc66_duplicate_notification_attempts_are_separate_batches():
    payload = {
        "user_id": "rc66-user",
        "channels": ["in_app"],
        "title": "RC66 duplicate attempt",
        "message": "Duplicate attempts should be observable as separate batches.",
        "payload": {
            "source": "rc66",
            "idempotency_key": "rc66-user:duplicate-attempt",
        },
    }

    first = client.post("/api/v1/notifications/deliver", json=payload)
    second = client.post("/api/v1/notifications/deliver", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200

    first_data = first.json()
    second_data = second.json()

    assert first_data["batch_id"] != second_data["batch_id"]
    assert first_data["messages"][0]["payload"]["idempotency_key"] == "rc66-user:duplicate-attempt"
    assert second_data["messages"][0]["payload"]["idempotency_key"] == "rc66-user:duplicate-attempt"
