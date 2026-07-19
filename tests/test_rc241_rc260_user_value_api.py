from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_rc241_rc260_vertical_slice():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post("/api/v1/user-value/clear", headers=headers)

        savings = client.post(
            "/api/v1/user-value/savings/events",
            headers=headers,
            json={
                "payload": {
                    "user_id": user_id,
                    "deal_id": "d1",
                    "reference_price": 1000,
                    "paid_price": 700,
                }
            },
        ).json()
        assert savings["recorded"] is True

        dashboard = client.post(
            "/api/v1/user-value/dashboard",
            headers=headers,
            json={
                "payload": {
                    "user_id": user_id,
                    "recommendation_count": 10,
                    "accepted_count": 5,
                    "purchase_count": 2,
                }
            },
        ).json()

    assert dashboard["total_savings"] == 300
