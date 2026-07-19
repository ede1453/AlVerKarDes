from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_user_activity_vertical_slice_from_recommendation_click_to_adjustment():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post("/api/v1/user-activity/clear", headers=headers)

        recommendation_response = client.post(
            "/api/v1/recommendations/recommend",
            json={
                "query": "MacBook Air",
                "user_id": user_id,
                "candidates": [
                    {"product_key": "macbook-air", "product_name": "MacBook Air", "score": 75, "price": "949.00"},
                    {"product_key": "iphone", "product_name": "iPhone", "score": 80, "price": "999.00"},
                ],
            },
        )
        assert recommendation_response.status_code == 200

        client.post(
            "/api/v1/user-activity/record",
            headers=headers,
            json={
                "user_id": user_id,
                "event_type": "recommendation_clicked",
                "product_key": "macbook-air",
                "recommendation_id": recommendation_response.json()["items"][0]["recommendation_id"],
            },
        )

        adjusted_response = client.post(
            "/api/v1/user-activity/recommendations/adjust",
            headers=headers,
            json={
                "user_id": user_id,
                "recommendations": recommendation_response.json()["items"],
            },
        )

    assert adjusted_response.status_code == 200
    assert adjusted_response.json()["adjusted_count"] == len(recommendation_response.json()["items"])
