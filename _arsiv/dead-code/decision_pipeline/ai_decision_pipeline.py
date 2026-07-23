from dataclasses import dataclass, field

from app.domains.consumer_intelligence.consumer_intelligence_service import (
    ConsumerIntelligenceService,
)


@dataclass
class AIDecisionPipelineInput:
    deal_score: int
    authenticity_score: int
    recommendation: str
    recommendation_confidence: int
    trend_direction: str | None = None
    store_trust_score: int | None = None
    stock_status: str | None = None
    reason_codes: list[str] = field(default_factory=list)


@dataclass
class AIDecisionPipelineResult:
    pipeline_status: str
    final_decision: str
    confidence: int
    risk_level: str
    opportunity_level: str
    reason_codes: list[str]
    explanation: list[str]
    stages: list[dict]


class AIDecisionPipeline:
    def __init__(self, consumer_intelligence_service: ConsumerIntelligenceService | None = None):
        self.consumer_intelligence_service = consumer_intelligence_service or ConsumerIntelligenceService()

    def run(self, data: AIDecisionPipelineInput) -> AIDecisionPipelineResult:
        input_payload = {
            "deal_score": data.deal_score,
            "authenticity_score": data.authenticity_score,
            "recommendation": data.recommendation,
            "recommendation_confidence": data.recommendation_confidence,
            "trend_direction": data.trend_direction,
            "store_trust_score": data.store_trust_score,
            "stock_status": data.stock_status,
            "reason_codes": data.reason_codes,
        }

        stages = [
            {
                "name": "input_validation",
                "status": "PASSED",
                "data": {
                    "deal_score": data.deal_score,
                    "authenticity_score": data.authenticity_score,
                    "recommendation": data.recommendation,
                },
            }
        ]

        consumer_result = self.consumer_intelligence_service.evaluate(input_payload)

        stages.append(
            {
                "name": "consumer_intelligence",
                "status": "PASSED",
                "data": {
                    "final_decision": consumer_result["final_decision"],
                    "confidence": consumer_result["confidence"],
                    "risk_level": consumer_result["risk_level"],
                    "opportunity_level": consumer_result["opportunity_level"],
                },
            }
        )

        stages.append(
            {
                "name": "final_decision",
                "status": "PASSED",
                "data": {
                    "decision": consumer_result["final_decision"],
                },
            }
        )

        return AIDecisionPipelineResult(
            pipeline_status="PASSED",
            final_decision=consumer_result["final_decision"],
            confidence=consumer_result["confidence"],
            risk_level=consumer_result["risk_level"],
            opportunity_level=consumer_result["opportunity_level"],
            reason_codes=consumer_result["reason_codes"],
            explanation=consumer_result["explanation"],
            stages=stages,
        )
