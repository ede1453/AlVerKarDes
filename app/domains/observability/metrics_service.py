from app.domains.observability.metrics_engine import ObservabilityMetricsEngine
from app.domains.observability.metrics_serializer import serialize_observability_snapshot


class ObservabilityMetricsService:
    def __init__(self, engine: ObservabilityMetricsEngine | None = None):
        self.engine = engine or ObservabilityMetricsEngine()

    def snapshot(self, payload: dict | None = None):
        return serialize_observability_snapshot(self.engine.snapshot(payload or {}))
