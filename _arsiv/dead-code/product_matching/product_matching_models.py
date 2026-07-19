from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class ProductMatchCandidate:
    offer_id: str
    marketplace: str
    product_name: str
    normalized_product_name: str
    price: str
    currency: str
    metadata: dict = field(default_factory=dict)


@dataclass
class ProductMatchGroup:
    group_id: str
    canonical_name: str
    normalized_canonical_name: str
    match_confidence: int
    candidates: list[ProductMatchCandidate]
    created_at: datetime


@dataclass
class ProductMatchingResult:
    query: str
    group_count: int
    matched_offer_count: int
    groups: list[ProductMatchGroup]
    metadata: dict = field(default_factory=dict)


def normalize_product_name(value: str) -> str:
    return " ".join(value.strip().lower().replace("-", " ").split())


def create_group_id() -> str:
    return str(uuid4())


def now_utc():
    return datetime.now(timezone.utc)
