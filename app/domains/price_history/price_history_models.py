from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4


@dataclass
class PricePoint:
    id: str
    product_key: str
    marketplace: str
    price: Decimal
    currency: str
    observed_at: datetime
    metadata: dict = field(default_factory=dict)


@dataclass
class PriceHistorySummary:
    product_key: str
    currency: str | None
    point_count: int
    min_price: Decimal | None
    max_price: Decimal | None
    average_price: Decimal | None
    latest_price: Decimal | None
    trend: str
    points: list[PricePoint]


def create_price_point(data: dict) -> PricePoint:
    return PricePoint(
        id=data.get("id") or str(uuid4()),
        product_key=data["product_key"],
        marketplace=data.get("marketplace", "unknown"),
        price=Decimal(str(data["price"])),
        currency=data.get("currency", "EUR"),
        observed_at=data.get("observed_at") or datetime.now(timezone.utc),
        metadata=data.get("metadata", {}),
    )
