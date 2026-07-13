from app.domains.llm_provider_gateway.llm_provider_models import (
    LLMGatewayRequest,
    LLMGatewayResponse,
)
from app.domains.llm_provider_gateway.provider_interface import LLMProvider


class MockLLMProvider(LLMProvider):
    name = "mock"

    def generate(self, request: LLMGatewayRequest) -> LLMGatewayResponse:
        context = request.structured_context
        decision = context.get("assistant_decision") or "WATCH"
        product_name = (
            context.get("assistant_context", {}).get("product_name")
            or context.get("product_name")
            or "this product"
        )
        confidence = context.get("confidence")

        generated_text = self._generate_text(
            product_name=product_name,
            decision=decision,
            confidence=confidence,
            user_prompt=request.user_prompt,
        )

        return LLMGatewayResponse(
            provider=self.name,
            model=request.model,
            status="COMPLETED",
            generated_text=generated_text,
            safety_warnings=[],
            usage={
                "prompt_characters": len(request.system_prompt) + len(request.user_prompt),
                "completion_characters": len(generated_text),
                "mock": True,
            },
            metadata={
                "deterministic": True,
                "provider_mode": "offline_mock",
                "prompt_version": request.prompt_version,
            },
        )

    def _generate_text(
        self,
        *,
        product_name: str,
        decision: str,
        confidence,
        user_prompt: str,
    ) -> str:
        confidence_text = "" if confidence is None else f" Confidence is {confidence}/100."

        if decision == "BUY_NOW":
            return f"{product_name} is a buy-now candidate based on the provided signals.{confidence_text}"

        if decision in {"DO_NOT_BUY", "AVOID"}:
            return f"{product_name} should not be purchased from this offer based on the provided risk signals.{confidence_text}"

        if decision == "WAIT":
            return f"It is safer to wait before buying {product_name}.{confidence_text}"

        return f"{product_name} should be watched until stronger signals are available.{confidence_text}"
