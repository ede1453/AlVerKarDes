from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class WatchlistItem:
    id: str
    user_id: str
    product_key: str
    query: str
    target_price: str | None = None
    marketplaces: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=lambda: ["in_app"])
    status: str = "ACTIVE"
    last_evaluation: dict | None = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def create_watchlist_item_id() -> str:
    return str(uuid4())
