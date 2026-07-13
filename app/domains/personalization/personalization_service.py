from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.events.event_bus_service import EventBusService
from app.domains.personalization.personalization_engine import PersonalizationEngine
from app.domains.personalization.personalization_models import UserPreferenceProfile
from app.domains.personalization.personalization_repository import InMemoryPersonalizationRepository
from app.domains.personalization.personalization_serializer import (
    serialize_personalization_result,
    serialize_profile,
)


class PersonalizationService:
    def __init__(
        self,
        repository: InMemoryPersonalizationRepository | None = None,
        engine: PersonalizationEngine | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.repository = repository or InMemoryPersonalizationRepository()
        self.engine = engine or PersonalizationEngine()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def upsert_profile(self, payload: dict):
        profile = UserPreferenceProfile(
            user_id=payload["user_id"],
            preferred_marketplaces=payload.get("preferred_marketplaces", []),
            blocked_marketplaces=payload.get("blocked_marketplaces", []),
            preferred_brands=payload.get("preferred_brands", []),
            max_price=payload.get("max_price"),
            min_discount_percent=payload.get("min_discount_percent"),
            risk_tolerance=payload.get("risk_tolerance", "MEDIUM"),
            metadata=payload.get("metadata", {}),
        )
        saved = self.repository.upsert(profile)

        self.event_bus_service.publish(
            {
                "event_type": "personalization.profile_updated",
                "source": "personalization",
                "payload": {"user_id": saved.user_id},
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialize_profile(saved)

    def get_profile(self, user_id: str):
        profile = self.repository.get(user_id)
        if profile is None:
            return None
        return serialize_profile(profile)

    def score(self, payload: dict):
        profile = self.repository.get(payload["user_id"])
        if profile is None:
            profile = UserPreferenceProfile(user_id=payload["user_id"])

        result = self.engine.score(profile=profile, offers=payload.get("offers", []))
        serialized = serialize_personalization_result(result)

        self.event_bus_service.publish(
            {
                "event_type": "personalization.scored",
                "source": "personalization",
                "payload": {
                    "user_id": serialized["user_id"],
                    "scored_count": serialized["scored_count"],
                    "top_offer": serialized["top_offer"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def score_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="personalization_score",
            payload={
                "user_id": payload["user_id"],
                "offers": payload.get("offers", []),
            },
        )
        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.score(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )

    def clear(self):
        self.repository.clear()
        return {"cleared": True}
