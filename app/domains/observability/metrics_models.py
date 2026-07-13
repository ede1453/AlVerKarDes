from dataclasses import dataclass, field


@dataclass
class ProviderMetric:
    provider: str
    health_status: str
    available: bool
    latency_ms: int
    success_rate: float
    failure_count: int


@dataclass
class OrchestrationMetric:
    status: str
    selected_provider: str | None
    fallback_used: bool
    attempt_count: int
    prompt_version: str


@dataclass
class AuditMetric:
    audit_enabled: bool
    persistence_mode: str
    prompt_version: str | None = None


@dataclass
class ObservabilitySnapshot:
    status: str
    providers: list[ProviderMetric] = field(default_factory=list)
    orchestration: OrchestrationMetric | None = None
    audit: AuditMetric | None = None
    metadata: dict = field(default_factory=dict)
