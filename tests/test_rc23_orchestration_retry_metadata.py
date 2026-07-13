from app.domains.llm_orchestration.orchestration_service import LLMOrchestrationService


def test_orchestration_result_includes_retry_decision_metadata():
    data = LLMOrchestrationService().run(
        {
            "preferred_provider": "openai",
            "fallback_providers": ["mock"],
            "model": "mock-shopping-explainer",
            "system_prompt": "Explain safely.",
            "user_prompt": "Explain BUY_NOW.",
            "guardrails": ["Do not change assistant_decision."],
            "structured_context": {
                "assistant_decision": "BUY_NOW",
                "assistant_context": {"product_name": "MacBook Air"},
                "prompt_version": "shopping_v1",
            },
            "prompt_version": "shopping_v1",
            "max_attempts": 2,
            "timeout_ms": 1000,
        }
    )

    assert data["status"] == "COMPLETED"
    assert data["attempts"][0]["retry_decision"]["should_retry"] is True
    assert data["attempts"][0]["retry_decision"]["reason"] == "RETRYABLE_STATUS"
    assert data["metadata"]["retry_policy"] == "exponential_backoff"
