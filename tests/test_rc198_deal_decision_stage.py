from app.domains.commerce_pipeline.service import CommercePipelineService


def test_rc198_deal_decision_stage():
    service = CommercePipelineService()
    result = service.evaluate_deals(
        quality_result={
            "offers":[{
                "source_id":"amazon",
                "canonical_product_key":"product-1",
                "price":700,
                "normalized_price":700,
                "currency":"EUR",
                "historical_prices":[950,1000,1050,980],
                "claimed_original_price":1000,
                "source_confidence":90,
                "freshness_status":"FRESH",
                "anomalous":False,
                "shipping_cost":0,
                "review_reliability":80,
            }]
        }
    )
    assert result["recommendation"]["decision"] == "BUY"
