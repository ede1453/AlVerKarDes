from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class DecisionFeedbackCreate:
    user_id: str
    decision_id: str | None = None
    product_id: str | None = None
    offer_id: str | None = None
    feedback_type: str = "HELPFUL"
    rating: int | None = None
    comment: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class DecisionFeedbackRecord:
    id: str
    user_id: str
    decision_id: str | None
    product_id: str | None
    offer_id: str | None
    feedback_type: str
    rating: int | None
    comment: str | None
    metadata: dict
    created_at: datetime


@dataclass
class FeedbackLearningSummary:
    total_feedback_count: int
    helpful_count: int
    not_helpful_count: int
    purchased_count: int
    ignored_count: int
    average_rating: float | None
    learning_signal: str
    confidence_adjustment: int
    reason_codes: list[str]


def create_feedback_record(data: DecisionFeedbackCreate) -> DecisionFeedbackRecord:
    return DecisionFeedbackRecord(
        id=str(uuid4()),
        user_id=data.user_id,
        decision_id=data.decision_id,
        product_id=data.product_id,
        offer_id=data.offer_id,
        feedback_type=data.feedback_type,
        rating=data.rating,
        comment=data.comment,
        metadata=dict(data.metadata),
        created_at=datetime.now(timezone.utc),
    )
