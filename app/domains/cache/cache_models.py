from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CacheEntry:
    key: str
    value: dict
    ttl_seconds: int
    created_at: datetime
    expires_at: datetime


@dataclass
class CacheLookupResult:
    hit: bool
    key: str
    value: dict | None
    metadata: dict = field(default_factory=dict)


@dataclass
class CacheStatus:
    enabled: bool
    backend: str
    entry_count: int
    hit_count: int
    miss_count: int
    hit_rate: float
    miss_rate: float
    metadata: dict = field(default_factory=dict)
