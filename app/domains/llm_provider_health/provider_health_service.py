from app.domains.llm_provider_health.provider_health_engine import ProviderHealthEngine
from app.domains.llm_provider_health.provider_health_models import (
    ProviderHealthCheckRequest,
)
from app.domains.llm_provider_health.provider_health_serializer import (
    serialize_provider_health_summary,
)


class ProviderHealthService:
    def __init__(self, engine: ProviderHealthEngine | None = None):
        self.engine = engine or ProviderHealthEngine()

    def check(self, payload: dict):
        summary = self.engine.check(
            ProviderHealthCheckRequest(
                providers=payload.get("providers", ["mock", "openai", "local"]),
                include_external_boundaries=payload.get("include_external_boundaries", True),
            )
        )

        return serialize_provider_health_summary(summary)
