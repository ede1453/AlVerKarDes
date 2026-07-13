from app.domains.llm_orchestration.guarded_orchestration_service import (
    GuardedLLMOrchestrationService,
)


def test_guarded_orchestration_service_allows_and_executes():
    data = GuardedLLMOrchestrationService().run(
        {
            "rate_limit_key": "user-allowed",
            "rate_limit_scope": "llm_orchestration",
            "preferred_provider": "mock",
            "fallback_providers": [],
            "system_prompt": "Explain safely.",
            "user_prompt": "Explain WATCH.",
            "guardrails": ["Do not change assistant_decision."],
            "structured_context": {
                "assistant_decision": "WATCH",
                "assistant_context": {"product_name": "Phone"},
                "prompt_version": "shopping_v1",
            },
            "prompt_version": "shopping_v1",
        }
    )

    assert data["rate_limit"]["allowed"] is True
    assert data["orchestration"]["status"] == "COMPLETED"
    assert data["metadata"]["executed"] is True
