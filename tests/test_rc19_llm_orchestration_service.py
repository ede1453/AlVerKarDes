from app.domains.llm_orchestration.orchestration_service import LLMOrchestrationService


def test_orchestration_service_serializes_result():
    data = LLMOrchestrationService().run(
        {
            "preferred_provider": "mock",
            "fallback_providers": [],
            "system_prompt": "Explain safely.",
            "user_prompt": "Explain WATCH.",
            "guardrails": ["Do not change assistant_decision."],
            "structured_context": {
                "assistant_decision": "WATCH",
                "assistant_context": {"product_name": "Phone"},
            },
            "prompt_version": "shopping_v1",
        }
    )

    assert data["status"] == "COMPLETED"
    assert data["selected_provider"] == "mock"
    assert data["prompt_version"] == "shopping_v1"
