from app.domains.commerce_pipeline.service import CommercePipelineService


def test_rc199_persist_best_deal():
    service = CommercePipelineService()
    result = service.persist_best_deal(
        intelligence_result={
            "ranking":{
                "opportunities":[{
                    "source_id":"amazon",
                    "canonical_product_key":"product-1",
                    "price":700,
                    "effective_price":700,
                    "historical_prices":[950,1000,1050,980],
                    "claimed_original_price":1000,
                    "source_confidence":90,
                    "freshness_status":"FRESH",
                    "anomaly_detected":False,
                    "review_reliability":80,
                }]
            }
        },
        user_id="user-1",
    )
    assert result["operations"]["stored_count"] == 1
    assert result["persistence"]["persisted"] is True
