from app.domains.llm_provider_gateway.provider_registry import LLMProviderRegistry
from app.domains.llm_provider_health.provider_health_models import (
    ProviderHealthCheckRequest,
    ProviderHealthSummary,
)
from app.domains.llm_provider_health.provider_health_probe import ProviderHealthProbe


class ProviderHealthEngine:
    def __init__(
        self,
        probe: ProviderHealthProbe | None = None,
        provider_registry: LLMProviderRegistry | None = None,
    ):
        self.probe = probe or ProviderHealthProbe()
        self.provider_registry = provider_registry or LLMProviderRegistry()

    def check(self, request: ProviderHealthCheckRequest) -> ProviderHealthSummary:
        known_providers = set(self.provider_registry.list_provider_names())
        requested_providers = request.providers or self.provider_registry.list_provider_names()

        statuses = []

        for provider in requested_providers:
            if provider not in known_providers:
                statuses.append(
                    self._unknown_provider_status(provider)
                )
                continue

            status = self.probe.probe(provider)

            if not request.include_external_boundaries and status.metadata.get("external_boundary"):
                continue

            statuses.append(status)

        healthy_count = sum(1 for item in statuses if item.status == "HEALTHY")
        degraded_count = sum(1 for item in statuses if item.status == "DEGRADED")
        unavailable_count = sum(1 for item in statuses if item.status == "UNAVAILABLE")

        overall_status = "HEALTHY"
        if unavailable_count > 0:
            overall_status = "UNAVAILABLE"
        elif degraded_count > 0:
            overall_status = "DEGRADED"

        return ProviderHealthSummary(
            status=overall_status,
            healthy_count=healthy_count,
            degraded_count=degraded_count,
            unavailable_count=unavailable_count,
            providers=statuses,
        )

    def _unknown_provider_status(self, provider: str):
        from app.domains.llm_provider_health.provider_health_models import ProviderHealthStatus

        return ProviderHealthStatus(
            provider=provider,
            status="UNAVAILABLE",
            available=False,
            latency_ms=0,
            success_rate=0.0,
            failure_count=1,
            last_error="PROVIDER_NOT_REGISTERED",
            metadata={
                "known_provider": False,
            },
        )
