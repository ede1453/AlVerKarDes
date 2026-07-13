from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class DealDetectionResult:
    deal_id: str
    product_key: str
    offer: dict
    deal_level: str
    deal_score: int
    price_signal: str
    personalization_signal: str
    confidence: int
    reasons: list[str]
    next_actions: list[str]
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def create_deal_id() -> str:
    return str(uuid4())
