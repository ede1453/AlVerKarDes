from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4


@dataclass
class MarketplaceOfferInput:
    marketplace: str
    seller: str
    product_name: str
    price: Decimal
    currency: str = "EUR"
    url: str | None = None
    availability: str = "UNKNOWN"
    metadata: dict = field(default_factory=dict)


@dataclass
class MarketplaceOffer:
    id: str
    marketplace: str
    seller: str
    product_name: str
    normalized_product_name: str
    price: Decimal
    currency: str
    url: str | None
    availability: str
    metadata: dict
    collected_at: datetime


@dataclass
class MarketplaceAggregationResult:
    query: str
    normalized_query: str
    offer_count: int
    marketplaces: list[str]
    min_price: Decimal | None
    max_price: Decimal | None
    currency: str | None
    offers: list[MarketplaceOffer]


def normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def create_marketplace_offer(data: MarketplaceOfferInput) -> MarketplaceOffer:
    return MarketplaceOffer(
        id=str(uuid4()),
        marketplace=data.marketplace,
        seller=data.seller,
        product_name=data.product_name,
        normalized_product_name=normalize_text(data.product_name),
        price=Decimal(str(data.price)),
        currency=data.currency,
        url=data.url,
        availability=data.availability,
        metadata=dict(data.metadata),
        collected_at=datetime.now(timezone.utc),
    )
