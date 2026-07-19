from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc201_rc205_vertical_slice():
    # CLIENT-002d: POST /deal-feed/query no longer reads from the in-memory
    # _service._deals store this test ingests into -- it was rewired to
    # read REAL ingested market.Price data (RealDealFeedSourceService),
    # closing WIKI_ROOT/07-Issues-Risks/Deal-Feed-Kopuk-Veri-Kaynagi-CLIENT-002b.
    # The old ingest->query round trip this test exercised is therefore no
    # longer a valid assertion (query now returns whatever's really been
    # ingested platform-wide, not just this test's one manually-POSTed
    # deal) -- see tests/test_client_002d_real_deal_feed.py for the new
    # real-data coverage of /query. This test still exercises the
    # ingest_deals()/_deals path (unchanged, untouched) via its other real
    # consumer, GET /deal-feed/deals/{deal_id}.
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
    deal_id = ingested.json()["deals"][0]["deal_id"]

    fetched = client.get(f"/api/v1/deal-feed/deals/{deal_id}")

    assert fetched.status_code == 200
    assert fetched.json()["canonical_product_key"] == "product-1"
    assert fetched.json()["brand"] == "apple"
