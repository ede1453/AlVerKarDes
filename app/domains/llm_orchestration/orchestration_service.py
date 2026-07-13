from app.domains.llm_audit_trace.llm_audit_service import LLMAuditTraceService
from app.domains.llm_orchestration.orchestration_audit_adapter import (
    LLMOrchestrationAuditAdapter,
)
from app.domains.llm_orchestration.orchestration_engine import LLMOrchestrationEngine
from app.domains.llm_orchestration.orchestration_models import LLMOrchestrationRequest
from app.domains.llm_orchestration.orchestration_serializer import (
    serialize_llm_orchestration_result,
)
from app.domains.llm_provider_selection.provider_selection_service import (
    ProviderSelectionService,
)


class LLMOrchestrationService:
    def __init__(
        self,
        engine: LLMOrchestrationEngine | None = None,
        audit_service: LLMAuditTraceService | None = None,
        audit_adapter: LLMOrchestrationAuditAdapter | None = None,
        provider_selection_service: ProviderSelectionService | None = None,
    ):
        self.engine = engine or LLMOrchestrationEngine()
        self.audit_service = audit_service or LLMAuditTraceService()
        self.audit_adapter = audit_adapter or LLMOrchestrationAuditAdapter()
        self.provider_selection_service = provider_selection_service or ProviderSelectionService()

    def run(self, payload: dict):
        result = self.engine.run(
            LLMOrchestrationRequest(
                preferred_provider=payload.get("preferred_provider", "mock"),
                fallback_providers=payload.get("fallback_providers", ["mock"]),
                model=payload.get("model", "mock-shopping-explainer"),
                system_prompt=payload.get("system_prompt", ""),
                user_prompt=payload.get("user_prompt", ""),
                guardrails=payload.get("guardrails", []),
                structured_context=payload.get("structured_context", {}),
                max_attempts=payload.get("max_attempts", 2),
                prompt_version=payload.get("prompt_version", "shopping_v1"),
                timeout_ms=payload.get("timeout_ms"),
            )
        )

        return serialize_llm_orchestration_result(result)

    def run_with_intelligent_selection(self, payload: dict):
        selection = self.provider_selection_service.select(
            {
                "candidate_providers": payload.get("candidate_providers", ["mock", "openai", "local"]),
                "preferred_provider": payload.get("preferred_provider"),
                "require_available": payload.get("require_available", True),
                "max_latency_ms": payload.get("max_latency_ms"),
            }
        )

        if selection["selected_provider"] is None:
            return {
                "selection": selection,
                "orchestration": {
                    "status": "FAILED",
                    "selected_provider": None,
                    "generated_text": "",
                    "attempts": [],
                    "fallback_used": False,
                    "prompt_version": payload.get("prompt_version", "shopping_v1"),
                    "metadata": {
                        "reason": "NO_ELIGIBLE_PROVIDER",
                    },
                },
            }

        orchestration_payload = dict(payload)
        orchestration_payload["preferred_provider"] = selection["selected_provider"]
        orchestration_payload["fallback_providers"] = selection["fallback_providers"]
        orchestration_payload["max_attempts"] = max(
            1,
            min(
                payload.get("max_attempts", 2),
                1 + len(selection["fallback_providers"]),
            ),
        )

        return {
            "selection": selection,
            "orchestration": self.run(orchestration_payload),
        }

    async def run_with_audit(self, payload: dict):
        orchestration_result = self.run(payload)
        audit_payload = self.audit_adapter.build_audit_payload(
            orchestration_request=payload,
            orchestration_result=orchestration_result,
        )

        audit_trace = await self.audit_service.create_from_gateway_payload(
            request_payload=audit_payload["request_payload"],
            gateway_response=audit_payload["gateway_response"],
        )

        return {
            "orchestration": orchestration_result,
            "audit_trace": audit_trace,
        }
