from app.domains.decision_pipeline.ai_decision_pipeline import (
    AIDecisionPipeline,
    AIDecisionPipelineInput,
)
from app.domains.decision_pipeline.ai_decision_pipeline_serializer import (
    serialize_ai_decision_pipeline,
)


class AIDecisionPipelineService:
    def __init__(self, pipeline: AIDecisionPipeline | None = None):
        self.pipeline = pipeline or AIDecisionPipeline()

    def run(self, payload: dict):
        result = self.pipeline.run(
            AIDecisionPipelineInput(
                deal_score=payload["deal_score"],
                authenticity_score=payload["authenticity_score"],
                recommendation=payload["recommendation"],
                recommendation_confidence=payload["recommendation_confidence"],
                trend_direction=payload.get("trend_direction"),
                store_trust_score=payload.get("store_trust_score"),
                stock_status=payload.get("stock_status"),
                reason_codes=payload.get("reason_codes", []),
            )
        )

        return serialize_ai_decision_pipeline(result)
