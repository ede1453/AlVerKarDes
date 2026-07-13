from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.events.event_bus_service import EventBusService
from app.domains.smart_alerts.smart_alert_engine import SmartAlertEngine
from app.domains.smart_alerts.smart_alert_models import SmartAlertDecision, create_alert_id
from app.domains.smart_alerts.smart_alert_serializer import serialize_smart_alert


class SmartAlertService:
    def __init__(
        self,
        engine: SmartAlertEngine | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.engine = engine or SmartAlertEngine()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def evaluate(self, payload: dict):
        data = self.engine.decide(
            user_id=payload.get("user_id"),
            product_key=payload["product_key"],
            deal_detection=payload.get("deal_detection"),
            price_prediction=payload.get("price_prediction"),
            personalization=payload.get("personalization"),
            channels=payload.get("channels"),
        )

        decision = SmartAlertDecision(
            alert_id=create_alert_id(),
            user_id=payload.get("user_id"),
            product_key=payload["product_key"],
            should_alert=data["should_alert"],
            alert_level=data["alert_level"],
            alert_score=data["alert_score"],
            title=data["title"],
            message=data["message"],
            channels=data["channels"],
            reasons=data["reasons"],
            metadata={"smart_alert_version": "smart_alert_v1"},
        )

        serialized = serialize_smart_alert(decision)

        self.event_bus_service.publish(
            {
                "event_type": "smart_alert.evaluated",
                "source": "smart_alerts",
                "payload": {
                    "alert_id": serialized["alert_id"],
                    "user_id": serialized["user_id"],
                    "product_key": serialized["product_key"],
                    "should_alert": serialized["should_alert"],
                    "alert_level": serialized["alert_level"],
                    "alert_score": serialized["alert_score"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def evaluate_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="smart_alert",
            payload={
                "user_id": payload.get("user_id"),
                "product_key": payload["product_key"],
                "deal_detection": payload.get("deal_detection"),
                "price_prediction": payload.get("price_prediction"),
                "personalization": payload.get("personalization"),
                "channels": payload.get("channels"),
            },
        )
        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.evaluate(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
