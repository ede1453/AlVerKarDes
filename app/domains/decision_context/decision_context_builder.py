from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DecisionContextInput:
    product_id: str | None = None
    offer_id: str | None = None
    country: str = "DE"
    currency: str = "EUR"
    deal_score: int | None = None
    authenticity_score: int | None = None
    recommendation: str | None = None
    recommendation_confidence: int | None = None
    final_decision: str | None = None
    risk_level: str | None = None
    opportunity_level: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class DecisionContext:
    context_id: str
    created_at: datetime
    product_id: str | None
    offer_id: str | None
    market: dict
    scores: dict
    recommendation: dict
    decision: dict
    trace: list[dict]
    metadata: dict


class DecisionContextBuilder:
    def build(self, data: DecisionContextInput) -> DecisionContext:
        created_at = datetime.now(timezone.utc)

        trace = [
            {
                "stage": "context_created",
                "status": "PASSED",
            },
            {
                "stage": "scores_attached",
                "status": "PASSED",
                "data": {
                    "deal_score": data.deal_score,
                    "authenticity_score": data.authenticity_score,
                },
            },
            {
                "stage": "decision_attached",
                "status": "PASSED",
                "data": {
                    "final_decision": data.final_decision,
                    "risk_level": data.risk_level,
                    "opportunity_level": data.opportunity_level,
                },
            },
        ]

        context_id = self._build_context_id(
            product_id=data.product_id,
            offer_id=data.offer_id,
            created_at=created_at,
        )

        return DecisionContext(
            context_id=context_id,
            created_at=created_at,
            product_id=data.product_id,
            offer_id=data.offer_id,
            market={
                "country": data.country,
                "currency": data.currency,
            },
            scores={
                "deal_score": data.deal_score,
                "authenticity_score": data.authenticity_score,
            },
            recommendation={
                "recommendation": data.recommendation,
                "confidence": data.recommendation_confidence,
            },
            decision={
                "final_decision": data.final_decision,
                "risk_level": data.risk_level,
                "opportunity_level": data.opportunity_level,
                "reason_codes": list(data.reason_codes),
                "explanation": list(data.explanation),
            },
            trace=trace,
            metadata=dict(data.metadata),
        )

    def _build_context_id(self, *, product_id: str | None, offer_id: str | None, created_at: datetime) -> str:
        subject = offer_id or product_id or "anonymous"
        return f"decision-context::{subject}::{created_at.isoformat()}"
