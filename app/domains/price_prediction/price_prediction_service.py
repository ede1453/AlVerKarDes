from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.events.event_bus_service import EventBusService
from app.domains.price_prediction.price_prediction_engine import PricePredictionEngine
from app.domains.price_prediction.price_prediction_models import (
    PricePredictionResult,
    create_prediction_id,
)
from app.domains.price_prediction.price_prediction_serializer import serialize_price_prediction


class PricePredictionService:
    def __init__(
        self,
        engine: PricePredictionEngine | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.engine = engine or PricePredictionEngine()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def predict(self, payload: dict):
        data = self.engine.predict(
            product_key=payload["product_key"],
            price_history=payload.get("price_history", {}),
            horizon_days=payload.get("prediction_horizon_days", 7),
        )

        result = PricePredictionResult(
            prediction_id=create_prediction_id(),
            product_key=payload["product_key"],
            current_price=data["current_price"],
            predicted_price=data["predicted_price"],
            prediction_horizon_days=data["prediction_horizon_days"],
            direction=data["direction"],
            confidence=data["confidence"],
            recommendation_hint=data["recommendation_hint"],
            reasons=data["reasons"],
            metadata={"price_prediction_version": "price_prediction_v1"},
        )

        serialized = serialize_price_prediction(result)

        self.event_bus_service.publish(
            {
                "event_type": "price_prediction.completed",
                "source": "price_prediction",
                "payload": {
                    "prediction_id": serialized["prediction_id"],
                    "product_key": serialized["product_key"],
                    "direction": serialized["direction"],
                    "confidence": serialized["confidence"],
                    "recommendation_hint": serialized["recommendation_hint"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def predict_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="price_prediction",
            payload={
                "product_key": payload["product_key"],
                "price_history": payload.get("price_history", {}),
                "prediction_horizon_days": payload.get("prediction_horizon_days", 7),
            },
        )

        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.predict(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
