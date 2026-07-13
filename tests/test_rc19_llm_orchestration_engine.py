from app.domains.llm_orchestration.orchestration_engine import LLMOrchestrationEngine
from app.domains.llm_orchestration.orchestration_models import LLMOrchestrationRequest


def test_orchestration_engine_uses_mock_successfully():
    result = LLMOrchestrationEngine().run(
        LLMOrchestrationRequest(
            preferred_provider="mock",
            fallback_providers=[],
            system_prompt="Explain safely.",
            user_prompt="Explain BUY_NOW.",
            guardrails=["Do not change assistant_decision."],
            structured_context={
                "assistant_decision": "BUY_NOW",
                "assistant_context": {"product_name": "MacBook Air"},
            },
        )
    )

    assert result.status == "COMPLETED"
    assert result.selected_provider == "mock"
    assert result.fallback_used is False
    assert len(result.attempts) == 1


def test_orchestration_engine_falls_back_from_unconfigured_openai_to_mock():
    result = LLMOrchestrationEngine().run(
        LLMOrchestrationRequest(
            preferred_provider="openai",
            fallback_providers=["mock"],
            system_prompt="Explain safely.",
            user_prompt="Explain BUY_NOW.",
            guardrails=["Do not change assistant_decision."],
            structured_context={
                "assistant_decision": "BUY_NOW",
                "assistant_context": {"product_name": "MacBook Air"},
            },
            max_attempts=2,
        )
    )

    assert result.status == "COMPLETED"
    assert result.selected_provider == "mock"
    assert result.fallback_used is True
    assert [attempt.provider for attempt in result.attempts] == ["openai", "mock"]
