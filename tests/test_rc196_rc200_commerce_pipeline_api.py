from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers

def test_rc196_rc200_vertical_slice():
    with TestClient(app) as client:
        headers = auth_headers(client)
        client.post(
            "/api/v1/commerce-pipeline/clear", headers=headers
        )

        response = client.post(
            "/api/v1/commerce-pipeline/run",
            headers=headers,
            json={
                "marketplace":"amazon",
                "items":[{
                    "asin":"A1",
                    "title":"Laptop",
                    "detail_page_url":"https://example.test/a1",
                    "price":700,
                    "currency":"EUR",
                    "availability":"in_stock",
                    "observed_at":"2026-07-12T10:00:00+00:00",
                    "historical_prices":[950,1000,1050,980],
                    "claimed_original_price":1000,
                    "source_trust_score":90,
                    "verified_source":True,
                    "review_reliability":80,
                    "shipping_cost":0,
                    "canonical_product_key":"product-1"
                }],
                "target_currency":"EUR",
                "exchange_rates":{},
                "reference_time":"2026-07-12T12:00:00+00:00",
                "user_id":"user-1"
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["run"]["status"] == "COMPLETED"
        assert data["run"]["recommendation"]["decision"] == "BUY"

        run_id = data["run"]["run_id"]

        stored = client.get(
            f"/api/v1/commerce-pipeline/runs/{run_id}", headers=headers
        )
    assert stored.status_code == 200
