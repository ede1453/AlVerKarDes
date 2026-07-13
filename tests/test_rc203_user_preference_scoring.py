from app.domains.deal_feed.service import UserPreferenceScorer


def test_rc203_preferred_brand_and_category():
    result = UserPreferenceScorer().score(
        deal={
            "opportunity_score":70,
            "category":"laptop",
            "brand":"apple",
            "source_id":"amazon",
            "effective_price":900,
            "observed_discount_pct":25,
        },
        preferences={
            "preferred_categories":["laptop"],
            "preferred_brands":["apple"],
            "maximum_price":1000,
            "minimum_discount_pct":20,
        },
    )
    assert result["personalized_score"] == 95
    assert result["eligible"] is True

def test_rc203_blocked_source():
    result = UserPreferenceScorer().score(
        deal={
            "opportunity_score":90,
            "source_id":"unknown-shop",
            "effective_price":500,
        },
        preferences={
            "blocked_sources":["unknown-shop"]
        },
    )
    assert result["eligible"] is False
