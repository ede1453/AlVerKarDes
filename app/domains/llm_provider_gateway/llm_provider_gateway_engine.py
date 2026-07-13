from app.domains.llm_provider_gateway.llm_provider_models import (
    LLMGatewayRequest,
    LLMGatewayResponse,
)
from app.domains.llm_provider_gateway.llm_safety_guard import LLMSafetyGuard
from app.domains.llm_provider_gateway.provider_registry import LLMProviderRegistry


class LLMProviderGatewayEngine:
    def __init__(
        self,
        registry: LLMProviderRegistry | None = None,
        safety_guard: LLMSafetyGuard | None = None,
    ):
        self.registry = registry or LLMProviderRegistry()
        self.safety_guard = safety_guard or LLMSafetyGuard()

    def generate(self, request: LLMGatewayRequest) -> LLMGatewayResponse:
        warnings = self.safety_guard.validate(
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            guardrails=request.guardrails,
        )

        if warnings:
            return LLMGatewayResponse(
                provider=request.provider,
                model=request.model,
                status="BLOCKED",
                generated_text="",
                safety_warnings=warnings,
                usage={
                    "prompt_characters": len(request.system_prompt) + len(request.user_prompt),
                    "completion_characters": 0,
                    "mock": request.provider == "mock",
                },
                metadata={
                    "blocked_by": "LLMSafetyGuard",
                    "available_providers": self.registry.list_provider_names(),
                },
            )

        provider = self.registry.get(request.provider)

        if provider is None:
            return LLMGatewayResponse(
                provider=request.provider,
                model=request.model,
                status="PROVIDER_NOT_FOUND",
                generated_text="",
                safety_warnings=[],
                usage={
                    "prompt_characters": len(request.system_prompt) + len(request.user_prompt),
                    "completion_characters": 0,
                    "mock": False,
                },
                metadata={
                    "available_providers": self.registry.list_provider_names(),
                },
            )

        return provider.generate(request)
