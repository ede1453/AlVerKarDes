import pytest

from app.domains.personalized_intelligence.personalized_intelligence_service import (
    PersonalizedIntelligenceService,
)
from app.domains.personalized_intelligence.user_preference_repository import (
    InMemoryUserPreferenceRepository,
)


@pytest.mark.asyncio
async def test_personalized_service_saves_profile_and_personalizes_decision():
    service = PersonalizedIntelligenceService(repository=InMemoryUserPreferenceRepository())

    await service.save_profile(
        {
            "user_id": "user-1",
            "preferred_brands": ["apple"],
            "price_sensitivity": "MEDIUM",
            "minimum_confidence": 70,
        }
    )

    result = await service.personalize_decision(
        {
            "user_id": "user-1",
            "final_decision": "BUY_NOW",
            "confidence": 90,
            "product_brand": "apple",
            "opportunity_level": "HIGH",
        }
    )

    assert result["personalized_decision"] == "BUY_NOW"
    assert result["personalized_confidence"] == 95
