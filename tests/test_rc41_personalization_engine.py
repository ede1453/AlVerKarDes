from app.domains.personalization.personalization_engine import PersonalizationEngine
from app.domains.personalization.personalization_models import UserPreferenceProfile


def test_personalization_engine_prefers_marketplace_brand_and_budget():
    profile = UserPreferenceProfile(
        user_id="user-1",
        preferred_marketplaces=["saturn"],
        preferred_brands=["Apple"],
        max_price="1000.00",
    )

    result = PersonalizationEngine().score(
        profile=profile,
        offers=[
            {"id": "1", "marketplace": "amazon", "product_name": "Apple MacBook Air", "price": "999.00"},
            {"id": "2", "marketplace": "saturn", "product_name": "Apple MacBook Air", "price": "949.00"},
        ],
    )

    assert result.top_offer["marketplace"] == "saturn"
    assert result.top_offer["personalization_score"] == 95


def test_personalization_engine_penalizes_blocked_marketplace():
    profile = UserPreferenceProfile(user_id="user-1", blocked_marketplaces=["amazon"])
    result = PersonalizationEngine().score(
        profile=profile,
        offers=[{"id": "1", "marketplace": "amazon", "product_name": "MacBook Air", "price": "999.00"}],
    )

    assert result.offers[0].personalization_score == 0
    assert "BLOCKED_MARKETPLACE" in result.offers[0].reasons
