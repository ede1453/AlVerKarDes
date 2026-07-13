from app.domains.llm_orchestration.orchestration_audit_adapter import (
    LLMOrchestrationAuditAdapter,
)


def test_orchestration_audit_adapter_builds_audit_payload_from_successful_result():
    payload = LLMOrchestrationAuditAdapter().build_audit_payload(
        orchestration_request={
            "preferred_provider": "openai",
            "fallback_providers": ["mock"],
            "model": "mock-shopping-explainer",
            "system_prompt": "system",
            "user_prompt": "user",
            "guardrails": ["Do not change assistant_decision."],
            "structured_context": {
                "assistant_decision": "BUY_NOW",
                "prompt_version": "shopping_v1",
            },
            "prompt_version": "shopping_v1",
        },
        orchestration_result={
            "status": "COMPLETED",
            "selected_provider": "mock",
            "generated_text": "Generated text.",
            "fallback_used": True,
            "prompt_version": "shopping_v1",
            "attempts": [
                {
                    "provider": "openai",
                    "status": "PROVIDER_NOT_CONFIGURED",
                    "generated_text": "",
                    "safety_warnings": [],
                    "metadata": {},
                },
                {
                    "provider": "mock",
                    "status": "COMPLETED",
                    "generated_text": "Generated text.",
                    "safety_warnings": [],
                    "metadata": {"prompt_version": "shopping_v1"},
                },
            ],
            "metadata": {"attempt_count": 2},
        },
    )

    assert payload["request_payload"]["provider"] == "mock"
    assert payload["gateway_response"]["provider"] == "mock"
    assert payload["gateway_response"]["status"] == "COMPLETED"
    assert payload["gateway_response"]["usage"]["fallback_used"] is True
