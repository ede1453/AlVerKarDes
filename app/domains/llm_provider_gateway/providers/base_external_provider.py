from app.domains.llm_provider_gateway.llm_provider_models import (
    LLMGatewayRequest,
    LLMGatewayResponse,
)
from app.domains.llm_provider_gateway.provider_interface import LLMProvider


class ExternalProviderNotConfiguredError(RuntimeError):
    pass


class BaseExternalLLMProvider(LLMProvider):
    name = "external"

    def __init__(self, *, api_key: str | None = None, enabled: bool = False):
        self.api_key = api_key
        self.enabled = enabled

    def generate(self, request: LLMGatewayRequest) -> LLMGatewayResponse:
        if not self.enabled or not self.api_key:
            return LLMGatewayResponse(
                provider=self.name,
                model=request.model,
                status="PROVIDER_NOT_CONFIGURED",
                generated_text="",
                safety_warnings=[],
                usage={
                    "prompt_characters": len(request.system_prompt) + len(request.user_prompt),
                    "completion_characters": 0,
                    "mock": False,
                },
                metadata={
                    "provider_enabled": self.enabled,
                    "api_key_configured": bool(self.api_key),
                    "message": "External provider is intentionally disabled until explicitly configured.",
                },
            )

        return self._generate_external(request)

    def _generate_external(self, request: LLMGatewayRequest) -> LLMGatewayResponse:
        raise NotImplementedError("External provider implementation must override _generate_external.")
