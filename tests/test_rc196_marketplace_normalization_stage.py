from app.domains.commerce_pipeline.service import CommercePipelineService


def test_rc196_marketplace_normalization():
    service = CommercePipelineService()
    result = service.normalize_marketplace_items(
        marketplace="amazon",
        items=[{
            "asin":"A1",
            "title":"Laptop",
            "detail_page_url":"https://example.test/a1",
            "price":800,
            "currency":"EUR",
            "availability":"in_stock",
            "observed_at":"2026-07-12T10:00:00+00:00",
        }],
    )
    assert result["normalized_count"] == 1
    assert result["items"][0]["marketplace"] == "amazon"
