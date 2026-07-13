from app.domains.llm_orchestration.orchestration_service import LLMOrchestrationService
from app.domains.llm_provider_health.provider_health_service import ProviderHealthService
from app.domains.observability.metrics_models import (
    AuditMetric,
    ObservabilitySnapshot,
    OrchestrationMetric,
    ProviderMetric,
)


class ObservabilityMetricsEngine:
    def __init__(
        self,
        provider_health_service: ProviderHealthService | None = None,
        orchestration_service: LLMOrchestrationService | None = None,
    ):
        self.provider_health_service = provider_health_service or ProviderHealthService()
        self.orchestration_service = orchestration_service or LLMOrchestrationService()

    def snapshot(self, payload: dict | None = None) -> ObservabilitySnapshot:
        payload = payload or {}

        health = self.provider_health_service.check(
            {
                "providers": payload.get("providers", ["mock", "openai", "local"]),
                "include_external_boundaries": payload.get("include_external_boundaries", True),
            }
        )

        orchestration_payload = {
            "preferred_provider": payload.get("preferred_provider", "mock"),
            "fallback_providers": payload.get("fallback_providers", []),
            "model": payload.get("model", "mock-shopping-explainer"),
            "system_prompt": payload.get("system_prompt", "Observability health check."),
            "user_prompt": payload.get("user_prompt", "Explain WATCH."),
            "guardrails": payload.get("guardrails", ["Do not change assistant_decision."]),
            "structured_context": payload.get(
                "structured_context",
                {
                    "assistant_decision": "WATCH",
                    "assistant_context": {"product_name": "observability-check"},
                    "prompt_version": payload.get("prompt_version", "shopping_v1"),
                },
            ),
            "prompt_version": payload.get("prompt_version", "shopping_v1"),
            "max_attempts": payload.get("max_attempts", 1),
            "timeout_ms": payload.get("timeout_ms"),
        }

        orchestration = self.orchestration_service.run(orchestration_payload)

        provider_metrics = [
            ProviderMetric(
                provider=item["provider"],
                health_status=item["status"],
                available=item["available"],
                latency_ms=item["latency_ms"],
                success_rate=item["success_rate"],
                failure_count=item["failure_count"],
            )
            for item in health["providers"]
        ]

        orchestration_metric = OrchestrationMetric(
            status=orchestration["status"],
            selected_provider=orchestration["selected_provider"],
            fallback_used=orchestration["fallback_used"],
            attempt_count=orchestration["metadata"].get("attempt_count", len(orchestration["attempts"])),
            prompt_version=orchestration["prompt_version"],
        )

        audit_metric = AuditMetric(
            audit_enabled=True,
            persistence_mode=payload.get("audit_persistence_mode", "in_memory_or_db_endpoint"),
            prompt_version=orchestration["prompt_version"],
        )

        overall_status = "HEALTHY"
        if health["status"] == "UNAVAILABLE" or orchestration["status"] != "COMPLETED":
            overall_status = "UNAVAILABLE"
        elif health["status"] == "DEGRADED":
            overall_status = "DEGRADED"

        return ObservabilitySnapshot(
            status=overall_status,
            providers=provider_metrics,
            orchestration=orchestration_metric,
            audit=audit_metric,
            metadata={
                "health_status": health["status"],
                "provider_count": len(provider_metrics),
                "observability_version": "observability_v1",
            },
        )
