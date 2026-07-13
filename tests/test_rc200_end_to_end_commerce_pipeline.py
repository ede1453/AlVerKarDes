from app.domains.commerce_pipeline.service import CommercePipelineService


def test_rc200_end_to_end_pipeline():
    service = CommercePipelineService()

    result = service.run_pipeline(
        marketplace="amazon",
        items=[{
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
            "canonical_product_key":"product-1",
        }],
        target_currency="EUR",
        exchange_rates={},
        reference_time="2026-07-12T12:00:00+00:00",
        user_id="user-1",
    )

    assert result["executed"] is True
    assert result["run"]["status"] == "COMPLETED"
    assert result["run"]["recommendation"]["decision"] == "BUY"
    assert result["run"]["persistence"]["persisted"] is True
