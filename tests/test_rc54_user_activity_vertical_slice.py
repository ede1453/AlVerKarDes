from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_user_activity_vertical_slice_from_recommendation_click_to_adjustment():
    client.post("/api/v1/user-activity/clear")

    recommendation_response = client.post(
        "/api/v1/recommendations/recommend",
        json={
            "query": "MacBook Air",
            "user_id": "user-1",
            "candidates": [
                {"product_key": "macbook-air", "product_name": "MacBook Air", "score": 75, "price": "949.00"},
                {"product_key": "iphone", "product_name": "iPhone", "score": 80, "price": "999.00"},
            ],
        },
    )
    assert recommendation_response.status_code == 200

    client.post(
        "/api/v1/user-activity/record",
        json={
            "user_id": "user-1",
            "event_type": "recommendation_clicked",
            "product_key": "macbook-air",
            "recommendation_id": recommendation_response.json()["items"][0]["recommendation_id"],
        },
    )

    adjusted_response = client.post(
        "/api/v1/user-activity/recommendations/adjust",
        json={
            "user_id": "user-1",
            "recommendations": recommendation_response.json()["items"],
        },
    )

    assert adjusted_response.status_code == 200
    assert adjusted_response.json()["adjusted_count"] == len(recommendation_response.json()["items"])
