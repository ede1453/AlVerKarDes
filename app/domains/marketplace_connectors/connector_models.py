from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class MarketplaceConnectorQuery:
    query: str
    marketplace: str
    limit: int = 10
    locale: str = "de-DE"
    currency: str = "EUR"
    metadata: dict = field(default_factory=dict)


@dataclass
class MarketplaceConnectorOffer:
    id: str
    marketplace: str
    seller: str
    product_name: str
    price: str
    currency: str
    url: str | None = None
    availability: str = "UNKNOWN"
    metadata: dict = field(default_factory=dict)
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MarketplaceConnectorResult:
    marketplace: str
    query: str
    status: str
    offer_count: int
    offers: list[MarketplaceConnectorOffer]
    metadata: dict = field(default_factory=dict)


def create_offer_id() -> str:
    return str(uuid4())
