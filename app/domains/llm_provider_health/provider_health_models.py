from dataclasses import dataclass, field


@dataclass
class ProviderHealthCheckRequest:
    providers: list[str] = field(default_factory=lambda: ["mock", "openai", "local"])
    include_external_boundaries: bool = True


@dataclass
class ProviderHealthStatus:
    provider: str
    status: str
    available: bool
    latency_ms: int
    success_rate: float
    failure_count: int
    last_error: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ProviderHealthSummary:
    status: str
    healthy_count: int
    degraded_count: int
    unavailable_count: int
    providers: list[ProviderHealthStatus]
