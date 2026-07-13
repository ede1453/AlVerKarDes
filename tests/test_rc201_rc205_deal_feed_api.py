from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc201_rc205_vertical_slice():
    client.post("/api/v1/deal-feed/clear")

    ingested = client.post(
        "/api/v1/deal-feed/ingest",
        json={
            "deals":[
                {
                    "canonical_product_key":"product-1",
                    "source_id":"amazon",
                    "external_offer_id":"A1",
                    "price":700,
                    "currency":"EUR",
                    "confidence_score":90,
                    "opportunity_score":88,
                    "observed_discount_pct":30,
                    "brand":"apple",
                    "category":"laptop",
                    "effective_price":700
                }
            ]
        },
    )

    assert ingested.status_code == 200
    assert ingested.json()["stored_count"] == 1

    feed = client.post(
        "/api/v1/deal-feed/query",
        json={
            "preferences":{
                "preferred_brands":["apple"]
            },
            "minimum_confidence":70,
            "limit":10
        },
    )

    assert feed.status_code == 200
    assert feed.json()["feed_count"] == 1
