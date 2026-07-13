from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class UserProfile:
    user_id: str
    preferred_product_keys: list[str] = field(default_factory=list)
    avoided_product_keys: list[str] = field(default_factory=list)
    preferred_marketplaces: list[str] = field(default_factory=list)
    blocked_marketplaces: list[str] = field(default_factory=list)
    preferred_brands: list[str] = field(default_factory=list)
    risk_tolerance: str = "MEDIUM"
    profile_score: int = 0
    metadata: dict = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
