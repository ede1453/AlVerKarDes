from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_deal_summary_endpoint_returns_buy_response():
    response = client.post(
        "/api/v1/deals/summary",
        json={
            "prices": [
                {
                    "amount": "899.00",
                    "observed_at": "2026-06-15T00:00:00+00:00",
                },
                {
                    "amount": "849.00",
                    "observed_at": "2026-07-05T00:00:00+00:00",
                },
            ],
            "cross_store_min_amount": "849.00",
            "store_trust_score": 95,
            "stock_status": "in_stock",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["has_price_data"] is True
    assert data["recommendation"] == "BUY"
    assert data["deal_score"]["decision"] == "BUY"
    assert data["lowest_prices"]["lowest_30d"]["amount"] == "849.00"
