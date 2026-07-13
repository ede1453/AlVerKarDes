from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class UnifiedSearchRequest:
    query: str
    user_id: str | None = None
    marketplaces: list[str] = field(default_factory=list)
    offers: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class UnifiedSearchResult:
    search_id: str
    query: str
    user_id: str | None
    status: str
    aggregation: dict
    top_offer: dict | None
    candidate_count: int
    metadata: dict
    created_at: datetime


def create_search_id() -> str:
    return str(uuid4())


def now_utc():
    return datetime.now(timezone.utc)
