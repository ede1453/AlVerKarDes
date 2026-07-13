from dataclasses import dataclass


@dataclass
class MasterResolutionContext:
    title: str
    source: str
    url: str | None
    canonical_key: str
    master_product_id: str | None = None
    resolution_reason: str | None = None
    resolution_confidence: float = 0.0
