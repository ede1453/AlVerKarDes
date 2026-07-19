from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_rc66_duplicate_notification_attempts_are_separate_batches():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        payload = {
            "user_id": user_id,
            "channels": ["in_app"],
            "title": "RC66 duplicate attempt",
            "message": "Duplicate attempts should be observable as separate batches.",
            "payload": {
                "source": "rc66",
                "idempotency_key": "rc66-user:duplicate-attempt",
            },
        }

        first = client.post("/api/v1/notifications/deliver", headers=headers, json=payload)
        second = client.post("/api/v1/notifications/deliver", headers=headers, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200

    first_data = first.json()
    second_data = second.json()

    assert first_data["batch_id"] != second_data["batch_id"]
    assert first_data["messages"][0]["payload"]["idempotency_key"] == "rc66-user:duplicate-attempt"
    assert second_data["messages"][0]["payload"]["idempotency_key"] == "rc66-user:duplicate-attempt"
