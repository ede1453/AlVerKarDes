from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class UserActivityEvent:
    activity_id: str
    user_id: str
    event_type: str
    product_key: str | None = None
    recommendation_id: str | None = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UserFeedbackSummary:
    user_id: str
    event_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    preferred_product_keys: list[str]
    avoided_product_keys: list[str]
    metadata: dict = field(default_factory=dict)


def create_activity_id() -> str:
    return str(uuid4())
