from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class SmartAlertDecision:
    alert_id: str
    user_id: str | None
    product_key: str
    should_alert: bool
    alert_level: str
    alert_score: int
    title: str
    message: str
    channels: list[str]
    reasons: list[str]
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def create_alert_id() -> str:
    return str(uuid4())
