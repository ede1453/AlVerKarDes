from app.domains.llm_provider_gateway.llm_provider_models import (
    LLMGatewayRequest,
    LLMGatewayResponse,
)
from app.domains.llm_provider_gateway.providers.base_external_provider import (
    BaseExternalLLMProvider,
)


class LocalLLMProvider(BaseExternalLLMProvider):
    name = "local"

    def _generate_external(self, request: LLMGatewayRequest) -> LLMGatewayResponse:
        return LLMGatewayResponse(
            provider=self.name,
            model=request.model,
            status="NOT_IMPLEMENTED",
            generated_text="",
            safety_warnings=[],
            usage={
                "prompt_characters": len(request.system_prompt) + len(request.user_prompt),
                "completion_characters": 0,
                "mock": False,
            },
            metadata={
                "message": "Local provider boundary is present, but local inference is not implemented in RC16.",
                "contract_ready": True,
            },
        )
