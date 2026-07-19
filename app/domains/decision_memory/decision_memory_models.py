from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class DecisionMemoryCreate:
    user_id: str | None = None
    product_id: str | None = None
    offer_id: str | None = None
    country: str = "DE"
    final_decision: str = "WATCH"
    confidence: int = 0
    risk_level: str | None = None
    opportunity_level: str | None = None
    deal_score: int | None = None
    authenticity_score: int | None = None
    recommendation: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    decision_context: dict = field(default_factory=dict)


@dataclass
class DecisionMemoryRecord:
    id: str
    user_id: str | None
    product_id: str | None
    offer_id: str | None
    country: str
    final_decision: str
    confidence: int
    risk_level: str | None
    opportunity_level: str | None
    deal_score: int | None
    authenticity_score: int | None
    recommendation: str | None
    reason_codes: list[str]
    decision_context: dict
    generated_at: datetime
    outcome: dict | None = None


def create_decision_memory_record(data: DecisionMemoryCreate) -> DecisionMemoryRecord:
    return DecisionMemoryRecord(
        id=str(uuid4()),
        user_id=data.user_id,
        product_id=data.product_id,
        offer_id=data.offer_id,
        country=data.country,
        final_decision=data.final_decision,
        confidence=data.confidence,
        risk_level=data.risk_level,
        opportunity_level=data.opportunity_level,
        deal_score=data.deal_score,
        authenticity_score=data.authenticity_score,
        recommendation=data.recommendation,
        reason_codes=list(data.reason_codes),
        decision_context=dict(data.decision_context),
        generated_at=datetime.now(timezone.utc),
    )
