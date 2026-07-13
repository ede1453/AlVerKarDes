from app.domains.llm_provider_gateway.llm_provider_gateway_service import (
    LLMProviderGatewayService,
)


def test_llm_gateway_still_generates_with_mock_after_plugin_registry_refactor():
    data = LLMProviderGatewayService().generate(
        {
            "provider": "mock",
            "model": "mock-shopping-explainer",
            "system_prompt": "Explain safely.",
            "user_prompt": "Explain BUY_NOW.",
            "guardrails": ["Do not change assistant_decision."],
            "structured_context": {
                "assistant_decision": "BUY_NOW",
                "confidence": 94,
                "assistant_context": {
                    "product_name": "MacBook Air",
                },
            },
            "prompt_version": "shopping_v1",
        }
    )

    assert data["status"] == "COMPLETED"
    assert data["provider"] == "mock"
    assert data["metadata"]["prompt_version"] == "shopping_v1"
    assert "MacBook Air" in data["generated_text"]
