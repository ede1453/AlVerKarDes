from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_user_activity_api_record_summary_and_adjust():
    client.post("/api/v1/user-activity/clear")

    record_response = client.post(
        "/api/v1/user-activity/record",
        json={
            "user_id": "user-1",
            "event_type": "liked",
            "product_key": "macbook-air",
        },
    )
    assert record_response.status_code == 200

    summary_response = client.get("/api/v1/user-activity/users/user-1/summary")
    assert summary_response.status_code == 200
    assert summary_response.json()["preferred_product_keys"] == ["macbook-air"]

    adjust_response = client.post(
        "/api/v1/user-activity/recommendations/adjust",
        json={
            "user_id": "user-1",
            "recommendations": [
                {"product_key": "macbook-air", "product_name": "MacBook Air", "score": 75, "rationale": []}
            ],
        },
    )
    assert adjust_response.status_code == 200
    assert adjust_response.json()["items"][0]["score"] == 85


def test_user_activity_api_lists_events():
    client.post("/api/v1/user-activity/clear")
    client.post(
        "/api/v1/user-activity/record",
        json={"user_id": "user-2", "event_type": "alert_opened", "product_key": "macbook-air"},
    )

    response = client.get("/api/v1/user-activity/users/user-2/events")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
