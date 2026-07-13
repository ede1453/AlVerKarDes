from app.domains.events.event_bus_service import EventBusService
from app.domains.user_activity.activity_engine import UserActivityEngine
from app.domains.user_activity.activity_models import (
    UserActivityEvent,
    UserFeedbackSummary,
    create_activity_id,
)
from app.domains.user_activity.activity_repository import InMemoryUserActivityRepository
from app.domains.user_activity.activity_serializer import (
    serialize_activity_event,
    serialize_feedback_summary,
)


class UserActivityService:
    def __init__(
        self,
        repository: InMemoryUserActivityRepository | None = None,
        engine: UserActivityEngine | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.repository = repository or InMemoryUserActivityRepository()
        self.engine = engine or UserActivityEngine()
        self.event_bus_service = event_bus_service or EventBusService()

    def record(self, payload: dict):
        event = UserActivityEvent(
            activity_id=create_activity_id(),
            user_id=payload["user_id"],
            event_type=payload["event_type"],
            product_key=payload.get("product_key"),
            recommendation_id=payload.get("recommendation_id"),
            metadata=payload.get("metadata", {}),
        )
        saved = self.repository.add(event)
        serialized = serialize_activity_event(saved)

        self.event_bus_service.publish(
            {
                "event_type": "user_activity.recorded",
                "source": "user_activity",
                "payload": {
                    "activity_id": serialized["activity_id"],
                    "user_id": serialized["user_id"],
                    "event_type": serialized["event_type"],
                    "product_key": serialized["product_key"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def list_for_user(self, user_id: str):
        return {
            "items": [
                serialize_activity_event(event)
                for event in self.repository.list_for_user(user_id)
            ]
        }

    def summarize(self, user_id: str):
        data = self.engine.summarize(
            user_id=user_id,
            events=self.repository.list_for_user(user_id),
        )
        summary = UserFeedbackSummary(**data)
        return serialize_feedback_summary(summary)

    def adjust_recommendations(self, payload: dict):
        summary = self.summarize(payload["user_id"])
        return self.engine.recommendation_adjustment(
            summary=summary,
            recommendations=payload.get("recommendations", []),
        )

    def clear(self):
        self.repository.clear()
        return {"cleared": True}
