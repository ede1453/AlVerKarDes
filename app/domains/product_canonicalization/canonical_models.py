from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class CanonicalProduct:
    canonical_id: str
    canonical_key: str
    product_name: str
    brand: str | None
    model: str | None
    variant: str | None
    category: str | None
    confidence: int
    source_offer_ids: list[str]
    attributes: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CanonicalizationResult:
    query: str
    canonical_count: int
    products: list[CanonicalProduct]
    metadata: dict = field(default_factory=dict)


def create_canonical_id() -> str:
    return str(uuid4())
