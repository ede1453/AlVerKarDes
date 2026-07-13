from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class UserPreferenceProfile:
    user_id: str
    preferred_marketplaces: list[str] = field(default_factory=list)
    blocked_marketplaces: list[str] = field(default_factory=list)
    preferred_brands: list[str] = field(default_factory=list)
    max_price: str | None = None
    min_discount_percent: int | None = None
    risk_tolerance: str = "MEDIUM"
    metadata: dict = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PersonalizedOfferScore:
    offer_id: str
    marketplace: str
    product_name: str
    base_price: str
    personalization_score: int
    reasons: list[str]
    metadata: dict = field(default_factory=dict)


@dataclass
class PersonalizationResult:
    user_id: str
    scored_count: int
    top_offer: dict | None
    offers: list[PersonalizedOfferScore]
    metadata: dict = field(default_factory=dict)
