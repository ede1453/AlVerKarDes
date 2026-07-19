from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class ShoppingPipelineResult:
    pipeline_id: str
    user_id: str
    query: str
    status: str
    top_recommendation: dict | None
    search: dict
    canonicalization: dict
    recommendation: dict
    price_history: dict | None
    deal_detection: dict | None
    price_prediction: dict | None
    discount_intelligence: dict | None
    smart_alert: dict | None
    explanation: dict | None
    notification: dict | None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def create_pipeline_id() -> str:
    return str(uuid4())
