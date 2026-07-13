from app.domains.llm_provider_gateway.llm_provider_models import LLMGatewayRequest
from app.domains.llm_provider_gateway.providers.openai_provider import OpenAICompatibleProvider


def test_openai_provider_returns_not_configured_when_disabled():
    response = OpenAICompatibleProvider(api_key=None, enabled=False).generate(
        LLMGatewayRequest(
            provider="openai",
            model="gpt-test",
            system_prompt="Explain safely.",
            user_prompt="Explain.",
            guardrails=["Do not change assistant_decision."],
            structured_context={"assistant_decision": "WATCH"},
        )
    )

    assert response.status == "PROVIDER_NOT_CONFIGURED"
    assert response.provider == "openai"
    assert response.metadata["api_key_configured"] is False


def test_openai_provider_boundary_is_contract_ready_when_enabled():
    response = OpenAICompatibleProvider(api_key="test-key", enabled=True).generate(
        LLMGatewayRequest(
            provider="openai",
            model="gpt-test",
            system_prompt="Explain safely.",
            user_prompt="Explain.",
            guardrails=["Do not change assistant_decision."],
            structured_context={"assistant_decision": "WATCH"},
        )
    )

    assert response.status == "NOT_IMPLEMENTED"
    assert response.metadata["contract_ready"] is True
