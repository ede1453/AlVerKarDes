from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc140_rc144_vertical_slice():
    response = client.post(
        "/api/v1/price-quality/pipeline",
        json={
            "target_currency":"EUR",
            "exchange_rates":{"USD_EUR":0.92},
            "reference_time":"2026-07-10T20:00:00+00:00",
            "offers":[
                {
                    "source_id":"amazon",
                    "price":1000,
                    "currency":"EUR",
                    "observed_at":"2026-07-10T10:00:00+00:00",
                    "historical_prices":[950,1000,1050],
                    "source_trust_score":90,
                    "verified_source":True,
                    "shipping_cost":0
                },
                {
                    "source_id":"ebay",
                    "price":900,
                    "currency":"USD",
                    "observed_at":"2026-07-10T09:00:00+00:00",
                    "historical_prices":[950,1000,1050],
                    "source_trust_score":75,
                    "verified_source":False,
                    "shipping_cost":25
                }
            ]
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["evaluated_count"] == 2
    assert data["selection"]["selected"] is True
