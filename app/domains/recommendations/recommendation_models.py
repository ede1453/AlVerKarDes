from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class RecommendationItem:
    recommendation_id: str
    product_key: str
    product_name: str
    recommendation_type: str
    score: int
    rank: int
    rationale: list[str]
    source: dict
    metadata: dict = field(default_factory=dict)


@dataclass
class RecommendationResult:
    run_id: str
    user_id: str | None
    query: str
    status: str
    items: list[RecommendationItem]
    next_actions: list[str]
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def create_recommendation_id() -> str:
    return str(uuid4())


def create_recommendation_run_id() -> str:
    return str(uuid4())
