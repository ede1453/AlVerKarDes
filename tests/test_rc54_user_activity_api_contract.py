from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_user_activity_api_record_summary_and_adjust():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post("/api/v1/user-activity/clear", headers=headers)

        record_response = client.post(
            "/api/v1/user-activity/record",
            headers=headers,
            json={
                "user_id": user_id,
                "event_type": "liked",
                "product_key": "macbook-air",
            },
        )
        assert record_response.status_code == 200

        summary_response = client.get(
            f"/api/v1/user-activity/users/{user_id}/summary", headers=headers
        )
        assert summary_response.status_code == 200
        assert summary_response.json()["preferred_product_keys"] == ["macbook-air"]

        adjust_response = client.post(
            "/api/v1/user-activity/recommendations/adjust",
            headers=headers,
            json={
                "user_id": user_id,
                "recommendations": [
                    {"product_key": "macbook-air", "product_name": "MacBook Air", "score": 75, "rationale": []}
                ],
            },
        )

    assert adjust_response.status_code == 200
    assert adjust_response.json()["items"][0]["score"] == 85


def test_user_activity_api_lists_events():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post("/api/v1/user-activity/clear", headers=headers)
        client.post(
            "/api/v1/user-activity/record",
            headers=headers,
            json={"user_id": user_id, "event_type": "alert_opened", "product_key": "macbook-air"},
        )

        response = client.get(
            f"/api/v1/user-activity/users/{user_id}/events", headers=headers
        )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
