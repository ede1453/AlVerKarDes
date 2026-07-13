from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class PricePredictionResult:
    prediction_id: str
    product_key: str
    current_price: str | None
    predicted_price: str | None
    prediction_horizon_days: int
    direction: str
    confidence: int
    recommendation_hint: str
    reasons: list[str]
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def create_prediction_id() -> str:
    return str(uuid4())
