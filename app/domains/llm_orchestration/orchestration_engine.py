from app.domains.llm_orchestration.orchestration_models import (
    LLMOrchestrationAttempt,
    LLMOrchestrationRequest,
    LLMOrchestrationResult,
)
from app.domains.llm_orchestration.provider_routing_policy import ProviderRoutingPolicy
from app.domains.llm_provider_gateway.llm_provider_gateway_service import (
    LLMProviderGatewayService,
)
from app.domains.llm_retry_policy.retry_policy import ExponentialBackoffRetryPolicy
from app.domains.llm_retry_policy.retry_serializer import serialize_retry_decision
from app.domains.llm_retry_policy.timeout_classifier import TimeoutClassifier


class LLMOrchestrationEngine:
    def __init__(
        self,
        gateway_service: LLMProviderGatewayService | None = None,
        routing_policy: ProviderRoutingPolicy | None = None,
        retry_policy: ExponentialBackoffRetryPolicy | None = None,
        timeout_classifier: TimeoutClassifier | None = None,
    ):
        self.gateway_service = gateway_service or LLMProviderGatewayService()
        self.routing_policy = routing_policy or ProviderRoutingPolicy()
        self.retry_policy = retry_policy or ExponentialBackoffRetryPolicy()
        self.timeout_classifier = timeout_classifier or TimeoutClassifier()

    def run(self, request: LLMOrchestrationRequest) -> LLMOrchestrationResult:
        provider_order = self.routing_policy.build_provider_order(
            preferred_provider=request.preferred_provider,
            fallback_providers=request.fallback_providers,
        )

        attempts: list[LLMOrchestrationAttempt] = []
        max_attempts = max(1, min(request.max_attempts, len(provider_order)))

        for attempt_index, provider in enumerate(provider_order[:max_attempts]):
            gateway_response = self.gateway_service.generate(
                {
                    "provider": provider,
                    "model": request.model,
                    "system_prompt": request.system_prompt,
                    "user_prompt": request.user_prompt,
                    "guardrails": request.guardrails,
                    "structured_context": request.structured_context,
                    "prompt_version": request.prompt_version,
                }
            )

            provider_metadata = gateway_response.get("metadata", {})
            latency_ms = gateway_response.get("usage", {}).get("latency_ms")
            timeout_classification = self.timeout_classifier.classify(
                latency_ms=latency_ms,
                timeout_ms=request.timeout_ms,
                status=gateway_response["status"],
            )

            retry_decision = self.retry_policy.decide(
                status=gateway_response["status"],
                attempt_index=attempt_index,
            )

            attempt = LLMOrchestrationAttempt(
                provider=provider,
                status=gateway_response["status"],
                generated_text=gateway_response.get("generated_text", ""),
                safety_warnings=gateway_response.get("safety_warnings", []),
                metadata=provider_metadata,
                attempt_index=attempt_index,
                retry_decision=serialize_retry_decision(retry_decision),
                timeout_classification=timeout_classification,
            )
            attempts.append(attempt)

            if self.routing_policy.is_success(attempt.status):
                return LLMOrchestrationResult(
                    status="COMPLETED",
                    selected_provider=provider,
                    generated_text=attempt.generated_text,
                    attempts=attempts,
                    fallback_used=provider != request.preferred_provider,
                    prompt_version=request.prompt_version,
                    metadata={
                        "provider_order": provider_order,
                        "attempt_count": len(attempts),
                        "retry_policy": "exponential_backoff",
                        "timeout_ms": request.timeout_ms,
                    },
                )

            if not retry_decision.should_retry:
                if not self.routing_policy.should_try_next(attempt.status):
                    break

        return LLMOrchestrationResult(
            status="FAILED",
            selected_provider=None,
            generated_text="",
            attempts=attempts,
            fallback_used=len(attempts) > 1,
            prompt_version=request.prompt_version,
            metadata={
                "provider_order": provider_order,
                "attempt_count": len(attempts),
                "retry_policy": "exponential_backoff",
                "timeout_ms": request.timeout_ms,
            },
        )
