from app.domains.commerce_pipeline.service import CommercePipelineService


def test_rc200_marketplace_normalization_preserves_pipeline_context():
    service = CommercePipelineService()

    result = service.normalize_marketplace_items(
        marketplace="amazon",
        items=[
            {
                "asin": "A1",
                "title": "Laptop",
                "detail_page_url": "https://example.test/a1",
                "price": 700,
                "currency": "EUR",
                "availability": "in_stock",
                "observed_at": "2026-07-12T10:00:00+00:00",
                "historical_prices": [950, 1000, 1050, 980],
                "claimed_original_price": 1000,
                "source_trust_score": 90,
                "verified_source": True,
                "review_reliability": 80,
                "shipping_cost": 0,
                "canonical_product_key": "product-1",
            }
        ],
    )

    item = result["items"][0]

    assert item["marketplace"] == "amazon"
    assert item["historical_prices"] == [950, 1000, 1050, 980]
    assert item["claimed_original_price"] == 1000
    assert item["source_trust_score"] == 90
    assert item["verified_source"] is True
    assert item["review_reliability"] == 80
    assert item["canonical_product_key"] == "product-1"
