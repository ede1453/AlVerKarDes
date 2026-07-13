from app.domains.llm_provider_gateway.llm_provider_gateway_service import (
    LLMProviderGatewayService,
)


def test_llm_provider_gateway_service_serializes_response():
    data = LLMProviderGatewayService().generate(
        {
            "provider": "mock",
            "system_prompt": "Explain safely.",
            "user_prompt": "Explain WATCH.",
            "guardrails": ["Do not change assistant_decision."],
            "structured_context": {
                "assistant_decision": "WATCH",
                "confidence": 72,
                "assistant_context": {
                    "product_name": "Phone",
                },
            },
        }
    )

    assert data["status"] == "COMPLETED"
    assert data["provider"] == "mock"
    assert "Phone" in data["generated_text"]
