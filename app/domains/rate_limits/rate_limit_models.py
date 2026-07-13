from dataclasses import dataclass
from datetime import datetime


@dataclass
class RateLimitRule:
    scope: str
    limit: int
    window_seconds: int


@dataclass
class RateLimitCheck:
    allowed: bool
    scope: str
    key: str
    limit: int
    remaining: int
    reset_at: datetime
    reason: str


@dataclass
class RateLimitUsage:
    key: str
    scope: str
    count: int
    window_started_at: datetime
