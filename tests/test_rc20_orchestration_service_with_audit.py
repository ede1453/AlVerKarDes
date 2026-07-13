import pytest

from app.domains.llm_audit_trace.llm_audit_repository import InMemoryLLMAuditTraceRepository
from app.domains.llm_audit_trace.llm_audit_service import LLMAuditTraceService
from app.domains.llm_orchestration.orchestration_service import LLMOrchestrationService


@pytest.mark.asyncio
async def test_orchestration_service_run_with_audit_creates_trace():
    audit_service = LLMAuditTraceService(repository=InMemoryLLMAuditTraceRepository())
    service = LLMOrchestrationService(audit_service=audit_service)

    data = await service.run_with_audit(
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
        }
    )

    assert data["orchestration"]["status"] == "COMPLETED"
    assert data["orchestration"]["selected_provider"] == "mock"
    assert data["audit_trace"]["provider"] == "mock"
    assert data["audit_trace"]["assistant_decision"] == "BUY_NOW"
    assert data["audit_trace"]["prompt_version"] == "shopping_v1"
