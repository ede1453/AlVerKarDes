from dataclasses import dataclass, field


@dataclass
class ProviderSelectionRequest:
    candidate_providers: list[str] = field(default_factory=lambda: ["mock", "openai", "local"])
    preferred_provider: str | None = None
    require_available: bool = True
    max_latency_ms: int | None = None


@dataclass
class ProviderSelectionCandidate:
    provider: str
    health_status: str
    available: bool
    latency_ms: int
    success_rate: float
    selection_score: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class ProviderSelectionResult:
    selected_provider: str | None
    fallback_providers: list[str]
    candidates: list[ProviderSelectionCandidate]
    strategy: str
    metadata: dict = field(default_factory=dict)
