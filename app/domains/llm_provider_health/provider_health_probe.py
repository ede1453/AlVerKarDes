from time import perf_counter

from app.domains.llm_provider_gateway.llm_provider_gateway_service import (
    LLMProviderGatewayService,
)
from app.domains.llm_provider_health.provider_health_models import ProviderHealthStatus


class ProviderHealthProbe:
    def __init__(self, gateway_service: LLMProviderGatewayService | None = None):
        self.gateway_service = gateway_service or LLMProviderGatewayService()

    def probe(self, provider: str) -> ProviderHealthStatus:
        started = perf_counter()

        response = self.gateway_service.generate(
            {
                "provider": provider,
                "model": "mock-shopping-explainer",
                "system_prompt": "Health check.",
                "user_prompt": "Check provider health.",
                "guardrails": ["Do not change assistant_decision."],
                "structured_context": {
                    "assistant_decision": "WATCH",
                    "prompt_version": "shopping_v1",
                    "assistant_context": {
                        "product_name": "health-check",
                    },
                },
                "prompt_version": "shopping_v1",
            }
        )

        latency_ms = max(0, int((perf_counter() - started) * 1000))
        status = response["status"]

        if status == "COMPLETED":
            return ProviderHealthStatus(
                provider=provider,
                status="HEALTHY",
                available=True,
                latency_ms=latency_ms,
                success_rate=1.0,
                failure_count=0,
                metadata={
                    "gateway_status": status,
                    "provider_metadata": response.get("metadata", {}),
                },
            )

        if status in {"PROVIDER_NOT_CONFIGURED", "NOT_IMPLEMENTED"}:
            return ProviderHealthStatus(
                provider=provider,
                status="DEGRADED",
                available=False,
                latency_ms=latency_ms,
                success_rate=0.0,
                failure_count=1,
                last_error=status,
                metadata={
                    "gateway_status": status,
                    "provider_metadata": response.get("metadata", {}),
                    "external_boundary": True,
                },
            )

        return ProviderHealthStatus(
            provider=provider,
            status="UNAVAILABLE",
            available=False,
            latency_ms=latency_ms,
            success_rate=0.0,
            failure_count=1,
            last_error=status,
            metadata={
                "gateway_status": status,
                "provider_metadata": response.get("metadata", {}),
            },
        )
