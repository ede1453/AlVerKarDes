from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.user_profiles.user_profile_service import UserProfileService


def test_user_profile_service_applies_preferences_and_emits_event():
    reset_event_repository()
    service = UserProfileService()

    profile = service.apply_preferences(
        {
            "user_id": "user-1",
            "preferred_marketplaces": ["saturn"],
            "preferred_brands": ["Apple"],
            "risk_tolerance": "LOW",
        }
    )

    assert profile["preferred_marketplaces"] == ["saturn"]
    assert profile["profile_score"] > 0

    events = service.event_bus_service.list_recent(
        {"event_type": "user_profile.preferences_applied", "source": "user_profiles"}
    )
    assert events


def test_user_profile_service_merges_feedback():
    service = UserProfileService()

    profile = service.merge_feedback(
        {
            "user_id": "user-1",
            "feedback_summary": {
                "event_count": 2,
                "preferred_product_keys": ["macbook-air"],
                "avoided_product_keys": ["iphone"],
            },
        }
    )

    assert profile["preferred_product_keys"] == ["macbook-air"]
    assert profile["avoided_product_keys"] == ["iphone"]
