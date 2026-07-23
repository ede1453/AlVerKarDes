from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class ProviderScheduleCreate:
    name: str
    providers: list[str] = field(default_factory=lambda: ["mock", "openai", "local"])
    interval_seconds: int = 60
    enabled: bool = True


@dataclass
class ProviderScheduleRecord:
    id: str
    name: str
    providers: list[str]
    interval_seconds: int
    enabled: bool
    status: str
    created_at: datetime
    last_run_at: datetime | None = None
    last_result: dict | None = None
    locked_by: str | None = None
    locked_at: datetime | None = None


def create_provider_schedule(data: ProviderScheduleCreate) -> ProviderScheduleRecord:
    return ProviderScheduleRecord(
        id=str(uuid4()),
        name=data.name,
        providers=list(data.providers),
        interval_seconds=max(1, int(data.interval_seconds)),
        enabled=data.enabled,
        status="ACTIVE" if data.enabled else "DISABLED",
        created_at=datetime.now(timezone.utc),
    )
