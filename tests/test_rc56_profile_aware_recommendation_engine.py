from app.domains.profile_aware_recommendations.profile_aware_engine import ProfileAwareRecommendationEngine


def test_profile_aware_engine_boosts_profile_matches():
    result = ProfileAwareRecommendationEngine().enrich_signals(
        profile_context={
            "preferred_product_keys": ["macbook-air"],
            "preferred_marketplaces": ["saturn"],
            "preferred_brands": ["Apple"],
            "avoided_product_keys": [],
            "blocked_marketplaces": [],
            "profile_score": 60,
            "metadata": {"context_version": "user_profile_context_v1"},
        },
        base_recommendations=[
            {
                "product_key": "macbook-air",
                "product_name": "Apple MacBook Air",
                "marketplace": "saturn",
                "score": 70,
                "rationale": [],
                "source": {"marketplace": "saturn", "product_name": "Apple MacBook Air"},
            }
        ],
    )

    assert result["items"][0]["score"] == 100
    assert "PROFILE_PREFERRED_PRODUCT" in result["items"][0]["rationale"]


def test_profile_aware_engine_penalizes_blocked_marketplace():
    result = ProfileAwareRecommendationEngine().enrich_signals(
        profile_context={
            "blocked_marketplaces": ["amazon"],
            "avoided_product_keys": ["iphone"],
            "metadata": {},
        },
        base_recommendations=[
            {
                "product_key": "iphone",
                "product_name": "iPhone",
                "marketplace": "amazon",
                "score": 80,
                "rationale": [],
                "source": {"marketplace": "amazon"},
            }
        ],
    )

    assert result["items"][0]["score"] == 15
    assert result["items"][0]["recommendation_type"] == "AVOID_OR_WAIT"
