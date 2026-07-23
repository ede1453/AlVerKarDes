from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class ShoppingAgentDecision:
    agent_run_id: str
    user_id: str | None
    query: str
    decision: str
    confidence: int
    top_offer: dict | None
    personalization: dict | None
    search: dict | None
    matching: dict | None
    price_history: dict | None
    reasons: list[str]
    next_actions: list[str]
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def create_agent_run_id() -> str:
    return str(uuid4())
