from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class CrawlRequest:
    url: str
    connector: str = "mock"
    obey_robots_txt: bool = True
    allow_external_fetch: bool = False
    timeout_ms: int = 3000
    metadata: dict = field(default_factory=dict)


@dataclass
class CrawlResult:
    crawl_id: str
    url: str
    connector: str
    status: str
    allowed: bool
    content_type: str | None
    content: str | None
    extracted: dict
    warnings: list[str]
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def create_crawl_id() -> str:
    return str(uuid4())
