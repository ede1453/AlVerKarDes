from app.domains.explainability.explainability_engine import ExplainabilityEngine
from app.domains.explainability.explanation_models import ExplanationInput
from app.domains.explainability.explanation_serializer import serialize_explanation


class ExplanationService:
    def __init__(self, engine: ExplainabilityEngine | None = None):
        self.engine = engine or ExplainabilityEngine()

    def explain(self, payload: dict):
        result = self.engine.explain(
            ExplanationInput(
                final_decision=payload["final_decision"],
                confidence=payload["confidence"],
                risk_level=payload.get("risk_level"),
                opportunity_level=payload.get("opportunity_level"),
                reason_codes=payload.get("reason_codes", []),
                explanation=payload.get("explanation", []),
                scores=payload.get("scores", {}),
                market=payload.get("market", {}),
            )
        )

        return serialize_explanation(result)
