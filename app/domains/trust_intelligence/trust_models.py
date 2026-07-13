from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TrustSignal:
    source_type: str
    source_id: str
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    fraud_count: int = 0
    return_count: int = 0
    total_count: int = 0


@dataclass
class TrustProfile:
    entity_type: str
    entity_id: str
    trust_score: int
    reliability_score: int
    positive_count: int
    negative_count: int
    fraud_count: int
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TrustEvaluationInput:
    decision_id: str | None = None
    user_id: str | None = None
    store_id: str | None = None
    product_id: str | None = None
    base_confidence: int = 70
    final_decision: str = "WATCH"
    feedback_summary: dict = field(default_factory=dict)


@dataclass
class TrustEvaluationResult:
    decision_id: str | None
    user_trust_score: int
    community_score: int
    store_score: int
    product_score: int
    recommendation_confidence_adjustment: int
    final_confidence: int
    risk_modifier: str
    reason_codes: list[str]
