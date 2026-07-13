from app.domains.events.event_bus_service import EventBusService
from app.domains.user_profiles.user_profile_engine import UserProfileEngine
from app.domains.user_profiles.user_profile_models import UserProfile
from app.domains.user_profiles.user_profile_repository import InMemoryUserProfileRepository
from app.domains.user_profiles.user_profile_repository_factory import get_user_profile_repository
from app.domains.user_profiles.user_profile_serializer import serialize_user_profile


class UserProfileService:
    def __init__(
        self,
        repository: InMemoryUserProfileRepository | None = None,
        engine: UserProfileEngine | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.repository = repository or get_user_profile_repository()
        self.engine = engine or UserProfileEngine()
        self.event_bus_service = event_bus_service or EventBusService()

    def get_profile(self, user_id: str):
        profile = self.repository.get_or_create(user_id)
        return serialize_user_profile(profile)

    def apply_preferences(self, payload: dict):
        profile = self.get_profile(payload["user_id"])
        merged = self.engine.apply_manual_preferences(
            profile=profile,
            preferences=payload,
        )
        saved = self.repository.upsert(UserProfile(**self._model_fields(merged)))
        serialized = serialize_user_profile(saved)
        self._publish("user_profile.preferences_applied", serialized)
        return serialized

    def merge_feedback(self, payload: dict):
        profile = self.get_profile(payload["user_id"])
        merged = self.engine.merge_feedback_summary(
            profile=profile,
            feedback_summary=payload.get("feedback_summary", {}),
        )
        saved = self.repository.upsert(UserProfile(**self._model_fields(merged)))
        serialized = serialize_user_profile(saved)
        self._publish("user_profile.feedback_merged", serialized)
        return serialized

    def recommendation_context(self, user_id: str):
        profile = self.get_profile(user_id)
        return self.engine.recommendation_context(profile=profile)

    def clear(self):
        self.repository.clear()
        return {"cleared": True}

    def _model_fields(self, data: dict):
        allowed = {
            "user_id",
            "preferred_product_keys",
            "avoided_product_keys",
            "preferred_marketplaces",
            "blocked_marketplaces",
            "preferred_brands",
            "risk_tolerance",
            "profile_score",
            "metadata",
        }
        return {key: value for key, value in data.items() if key in allowed}

    def _publish(self, event_type: str, profile: dict):
        self.event_bus_service.publish(
            {
                "event_type": event_type,
                "source": "user_profiles",
                "payload": {
                    "user_id": profile["user_id"],
                    "profile_score": profile["profile_score"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )
