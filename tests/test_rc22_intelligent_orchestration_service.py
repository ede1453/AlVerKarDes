from app.domains.llm_orchestration.orchestration_service import LLMOrchestrationService


def test_orchestration_service_runs_with_intelligent_selection():
    data = LLMOrchestrationService().run_with_intelligent_selection(
        {
            "candidate_providers": ["mock", "openai", "local"],
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
        }
    )

    assert data["selection"]["selected_provider"] == "mock"
    assert data["orchestration"]["status"] == "COMPLETED"
    assert data["orchestration"]["selected_provider"] == "mock"
