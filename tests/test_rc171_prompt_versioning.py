from app.domains.llm_explanation_adapter.llm_explanation_service import (
    LLMExplanationAdapterService,
)
from app.domains.llm_provider_gateway.llm_provider_gateway_service import (
    LLMProviderGatewayService,
)


def test_llm_explanation_prepare_includes_prompt_version():
    data = LLMExplanationAdapterService().prepare(
        {
            "assistant_decision": "BUY_NOW",
            "headline": "Buy MacBook Air now",
            "summary": "The combined decision supports buying now.",
            "confidence": 94,
            "assistant_context": {"product_name": "MacBook Air"},
            "prompt_version": "shopping_v1",
        }
    )

    assert data["prompt_version"] == "shopping_v1"
    assert data["prompt"]["prompt_version"] == "shopping_v1"
    assert data["prompt"]["structured_context"]["prompt_version"] == "shopping_v1"


def test_llm_gateway_preserves_prompt_version_in_mock_metadata():
    data = LLMProviderGatewayService().generate(
        {
            "provider": "mock",
            "system_prompt": "Explain safely.",
            "user_prompt": "Explain BUY_NOW.",
            "guardrails": ["Do not change assistant_decision."],
            "structured_context": {
                "assistant_decision": "BUY_NOW",
                "prompt_version": "shopping_v1",
                "assistant_context": {"product_name": "MacBook Air"},
            },
        }
    )

    assert data["status"] == "COMPLETED"
    assert data["metadata"]["prompt_version"] == "shopping_v1"
