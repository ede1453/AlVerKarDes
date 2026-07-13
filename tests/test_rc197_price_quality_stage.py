from app.domains.commerce_pipeline.service import CommercePipelineService


def test_rc197_price_quality_stage():
    service = CommercePipelineService()
    result = service.enrich_price_quality(
        offers=[{
            "marketplace":"amazon",
            "external_offer_id":"A1",
            "product_title":"Laptop",
            "product_url":"https://example.test/a1",
            "price":800,
            "currency":"EUR",
            "observed_at":"2026-07-12T10:00:00+00:00",
            "historical_prices":[950,1000,1050],
            "source_trust_score":90,
            "verified_source":True,
            "shipping_cost":0,
        }],
        target_currency="EUR",
        exchange_rates={},
        reference_time="2026-07-12T12:00:00+00:00",
    )
    assert result["evaluated_count"] == 1
    assert result["selection"]["selected"] is True
