from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc241_rc260_vertical_slice():
    client.post("/api/v1/user-value/clear")

    savings = client.post(
        "/api/v1/user-value/savings/events",
        json={
            "payload":{
                "user_id":"u1",
                "deal_id":"d1",
                "reference_price":1000,
                "paid_price":700
            }
        },
    ).json()
    assert savings["recorded"] is True

    dashboard = client.post(
        "/api/v1/user-value/dashboard",
        json={
            "payload":{
                "user_id":"u1",
                "recommendation_count":10,
                "accepted_count":5,
                "purchase_count":2
            }
        },
    ).json()

    assert dashboard["total_savings"] == 300
