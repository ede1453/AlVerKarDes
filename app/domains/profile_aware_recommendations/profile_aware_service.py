from app.domains.events.event_bus_service import EventBusService
from app.domains.profile_aware_recommendations.profile_aware_engine import (
    ProfileAwareRecommendationEngine,
)
from app.domains.recommendations.recommendation_service import RecommendationService
from app.domains.user_profiles.user_profile_repository import UserProfileDBRepository
from app.domains.user_profiles.user_profile_service import UserProfileService


class ProfileAwareRecommendationService:
    def __init__(
        self,
        engine: ProfileAwareRecommendationEngine | None = None,
        recommendation_service: RecommendationService | None = None,
        user_profile_service: UserProfileService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.engine = engine or ProfileAwareRecommendationEngine()
        self.recommendation_service = recommendation_service or RecommendationService()
        # SCALE-008: user_profile_service isn't defaulted here (unlike the
        # others) because a DB-backed one needs a request-scoped `db` --
        # see recommend()'s `db` parameter, mirroring pipeline_service.py's
        # _real_offers(db, ...)/_real_price_history(db, ...) convention of
        # threading `db` through as a method argument rather than the
        # constructor. Explicitly injecting one here (e.g. an in-memory
        # test double) still works and takes priority over `db`.
        self.user_profile_service = user_profile_service
        self.event_bus_service = event_bus_service or EventBusService()

    async def recommend(self, payload: dict, db=None):
        user_id = payload["user_id"]
        profile_context = payload.get("profile_context")
        if profile_context is None:
            user_profile_service = self.user_profile_service or UserProfileService(
                repository=UserProfileDBRepository(db) if db is not None else None
            )
            profile_context = await user_profile_service.recommendation_context(user_id)

        base = self.recommendation_service.recommend(
            {
                "query": payload["query"],
                "user_id": user_id,
                "candidates": payload.get("candidates", []),
                "personalization": payload.get("personalization"),
                "discount_intelligence": payload.get("discount_intelligence"),
                "deal_detection": payload.get("deal_detection"),
                "price_prediction": payload.get("price_prediction"),
            }
        )

        enriched = self.engine.enrich_signals(
            profile_context=profile_context,
            base_recommendations=base.get("items", []),
        )

        result = {
            "user_id": user_id,
            "query": payload["query"],
            "base_status": base["status"],
            "status": enriched["status"],
            "items": enriched["items"],
            "profile_context": profile_context,
            "metadata": {
                "profile_aware_version": "profile_aware_recommendation_v1",
                "base_run_id": base.get("run_id"),
                **enriched["metadata"],
            },
        }

        self.event_bus_service.publish(
            {
                "event_type": "profile_aware_recommendation.generated",
                "source": "profile_aware_recommendations",
                "payload": {
                    "user_id": user_id,
                    "query": payload["query"],
                    "status": result["status"],
                    "item_count": len(result["items"]),
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return result
