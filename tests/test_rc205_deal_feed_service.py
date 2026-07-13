from app.domains.deal_feed.service import DealFeedService


def test_rc205_ingest_and_query_feed():
    service = DealFeedService()

    ingested = service.ingest_deals(
        deals=[
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
                "effective_price":700,
            }
        ]
    )

    assert ingested["stored_count"] == 1

    feed = service.get_feed(
        preferences={
            "preferred_brands":["apple"]
        },
        minimum_confidence=70,
    )

    assert feed["feed_count"] == 1
    assert feed["items"][0]["canonical_product_key"] == "product-1"
