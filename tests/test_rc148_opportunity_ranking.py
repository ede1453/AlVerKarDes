from app.domains.deal_intelligence.service import OpportunityRanker


def test_rc148_rank_opportunities():
    result = OpportunityRanker().rank(
        opportunities=[
            {
                "source_id":"a",
                "confidence_score":70,
                "observed_discount_pct":20,
                "source_confidence":80,
                "effective_price":900,
            },
            {
                "source_id":"b",
                "confidence_score":90,
                "observed_discount_pct":25,
                "source_confidence":90,
                "effective_price":920,
            },
        ]
    )
    assert result["ranked_count"] == 2
    assert result["best_opportunity"]["source_id"] == "b"
