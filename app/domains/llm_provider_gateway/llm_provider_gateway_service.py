from app.domains.llm_provider_gateway.llm_provider_gateway_engine import (
    LLMProviderGatewayEngine,
)
from app.domains.llm_provider_gateway.llm_provider_gateway_serializer import (
    serialize_llm_gateway_response,
)
from app.domains.llm_provider_gateway.llm_provider_models import LLMGatewayRequest


class LLMProviderGatewayService:
    def __init__(self, engine: LLMProviderGatewayEngine | None = None):
        self.engine = engine or LLMProviderGatewayEngine()

    def generate(self, payload: dict):
        prompt_version = payload.get("prompt_version") or payload.get("structured_context", {}).get("prompt_version", "shopping_v1")

        response = self.engine.generate(
            LLMGatewayRequest(
                provider=payload.get("provider", "mock"),
                model=payload.get("model", "mock-shopping-explainer"),
                system_prompt=payload.get("system_prompt", ""),
                user_prompt=payload.get("user_prompt", ""),
                guardrails=payload.get("guardrails", []),
                structured_context=payload.get("structured_context", {}),
                max_tokens=payload.get("max_tokens", 500),
                temperature=payload.get("temperature", 0.2),
                prompt_version=prompt_version,
            )
        )

        return serialize_llm_gateway_response(response)
