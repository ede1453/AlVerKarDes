from app.domains.user_profiles.user_profile_engine import UserProfileEngine


def test_user_profile_engine_merges_feedback_summary():
    result = UserProfileEngine().merge_feedback_summary(
        profile={"user_id": "user-1", "preferred_product_keys": [], "avoided_product_keys": [], "metadata": {}},
        feedback_summary={
            "event_count": 2,
            "preferred_product_keys": ["macbook-air"],
            "avoided_product_keys": ["iphone"],
        },
    )

    assert result["preferred_product_keys"] == ["macbook-air"]
    assert result["avoided_product_keys"] == ["iphone"]
    assert result["profile_score"] > 0


def test_user_profile_engine_builds_recommendation_context():
    context = UserProfileEngine().recommendation_context(
        profile={
            "user_id": "user-1",
            "preferred_marketplaces": ["saturn"],
            "blocked_marketplaces": [],
            "preferred_brands": ["Apple"],
            "preferred_product_keys": ["macbook-air"],
            "avoided_product_keys": [],
            "risk_tolerance": "LOW",
            "profile_score": 60,
        }
    )

    assert context["preferred_marketplaces"] == ["saturn"]
    assert context["risk_tolerance"] == "LOW"
