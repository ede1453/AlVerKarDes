from app.domains.personalized_intelligence.personalization_models import (
    PersonalizedDecisionInput,
    UserPreferenceProfile,
)
from app.domains.personalized_intelligence.personalized_intelligence_engine import (
    PersonalizedIntelligenceEngine,
)
from app.domains.personalized_intelligence.personalized_intelligence_serializer import (
    serialize_personalized_decision,
    serialize_user_profile,
)
from app.domains.personalized_intelligence.user_preference_repository import (
    UserPreferenceRepository,
)


class PersonalizedIntelligenceService:
    def __init__(
        self,
        repository: UserPreferenceRepository | None = None,
        engine: PersonalizedIntelligenceEngine | None = None,
    ):
        self.repository = repository or UserPreferenceRepository()
        self.engine = engine or PersonalizedIntelligenceEngine()

    async def save_profile(self, payload: dict):
        profile = UserPreferenceProfile(
            user_id=payload["user_id"],
            preferred_brands=payload.get("preferred_brands", []),
            avoided_brands=payload.get("avoided_brands", []),
            preferred_categories=payload.get("preferred_categories", []),
            price_sensitivity=payload.get("price_sensitivity", "MEDIUM"),
            minimum_confidence=payload.get("minimum_confidence", 70),
        )

        saved = await self.repository.save(profile)
        return serialize_user_profile(saved)

    async def get_profile(self, user_id: str):
        profile = await self.repository.get(user_id)
        if profile is None:
            return None
        return serialize_user_profile(profile)

    async def personalize_decision(self, payload: dict):
        profile = await self.repository.get_or_create(payload["user_id"])

        result = self.engine.personalize(
            profile=profile,
            decision=PersonalizedDecisionInput(
                user_id=payload["user_id"],
                final_decision=payload["final_decision"],
                confidence=payload["confidence"],
                product_brand=payload.get("product_brand"),
                product_category=payload.get("product_category"),
                current_price=payload.get("current_price"),
                risk_level=payload.get("risk_level"),
                opportunity_level=payload.get("opportunity_level"),
                reason_codes=payload.get("reason_codes", []),
            ),
        )

        return serialize_personalized_decision(result)
