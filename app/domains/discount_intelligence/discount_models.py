from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class DiscountIntelligenceResult:
    discount_id: str
    product_key: str
    current_price: str | None
    claimed_original_price: str | None
    effective_discount_percent: int | None
    discount_quality: str
    fake_discount_risk: str
    confidence: int
    reasons: list[str]
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def create_discount_id() -> str:
    return str(uuid4())
