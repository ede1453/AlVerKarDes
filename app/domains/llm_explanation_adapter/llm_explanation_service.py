from app.domains.llm_explanation_adapter.llm_explanation_engine import (
    LLMExplanationAdapterEngine,
)
from app.domains.llm_explanation_adapter.llm_explanation_models import (
    LLMExplanationInput,
)
from app.domains.llm_explanation_adapter.llm_explanation_serializer import (
    serialize_llm_explanation_draft,
)


class LLMExplanationAdapterService:
    def __init__(self, engine: LLMExplanationAdapterEngine | None = None):
        self.engine = engine or LLMExplanationAdapterEngine()

    def prepare(self, payload: dict):
        draft = self.engine.prepare(
            LLMExplanationInput(
                assistant_decision=payload["assistant_decision"],
                headline=payload["headline"],
                summary=payload["summary"],
                confidence=payload["confidence"],
                risk_level=payload.get("risk_level"),
                opportunity_level=payload.get("opportunity_level"),
                next_actions=payload.get("next_actions", []),
                reason_codes=payload.get("reason_codes", []),
                explanation=payload.get("explanation", []),
                assistant_context=payload.get("assistant_context", {}),
                language=payload.get("language", "en"),
                tone=payload.get("tone", "clear"),
                prompt_version=payload.get("prompt_version", "shopping_v1"),
            )
        )

        return serialize_llm_explanation_draft(draft)
