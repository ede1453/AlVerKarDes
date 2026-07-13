from app.domains.llm_provider_selection.provider_selection_engine import (
    IntelligentProviderSelectionEngine,
)
from app.domains.llm_provider_selection.provider_selection_models import (
    ProviderSelectionRequest,
)
from app.domains.llm_provider_selection.provider_selection_serializer import (
    serialize_provider_selection_result,
)


class ProviderSelectionService:
    def __init__(self, engine: IntelligentProviderSelectionEngine | None = None):
        self.engine = engine or IntelligentProviderSelectionEngine()

    def select(self, payload: dict):
        result = self.engine.select(
            ProviderSelectionRequest(
                candidate_providers=payload.get("candidate_providers", ["mock", "openai", "local"]),
                preferred_provider=payload.get("preferred_provider"),
                require_available=payload.get("require_available", True),
                max_latency_ms=payload.get("max_latency_ms"),
            )
        )

        return serialize_provider_selection_result(result)
