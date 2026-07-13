from app.domains.recommendations.recommendation_engine import RecommendationEngine


def test_recommendation_engine_ranks_best_candidate():
    result = RecommendationEngine().recommend(
        query="MacBook Air",
        user_id="user-1",
        candidates=[
            {"product_key": "macbook-air-1", "product_name": "MacBook Air Amazon", "marketplace": "amazon", "price": "999.00"},
            {"product_key": "macbook-air-2", "product_name": "MacBook Air Saturn", "marketplace": "saturn", "price": "949.00", "canonical_confidence": 95},
        ],
        personalization={"top_offer": {"marketplace": "saturn"}},
        discount_intelligence={"discount_quality": "EXCELLENT_REAL_DISCOUNT", "fake_discount_risk": "LOW"},
        deal_detection={"deal_level": "EXCELLENT_DEAL"},
        price_prediction={"recommendation_hint": "BUY_SOON"},
    )

    assert result["status"] == "COMPLETED"
    assert result["items"][0]["candidate"]["marketplace"] == "saturn"
    assert result["items"][0]["recommendation_type"] == "BEST_CHOICE"


def test_recommendation_engine_no_candidates():
    result = RecommendationEngine().recommend(
        query="Unknown",
        user_id=None,
        candidates=[],
    )

    assert result["status"] == "NO_RECOMMENDATIONS"
    assert result["items"] == []
