import pytest

from app.domains.llm_audit_trace.llm_audit_repository import InMemoryLLMAuditTraceRepository
from app.domains.llm_audit_trace.llm_audit_service import LLMAuditTraceService


@pytest.mark.asyncio
async def test_llm_audit_trace_stores_prompt_version():
    service = LLMAuditTraceService(repository=InMemoryLLMAuditTraceRepository())

    trace = await service.create_from_gateway_payload(
        request_payload={
            "provider": "mock",
            "model": "mock-shopping-explainer",
            "system_prompt": "system",
            "user_prompt": "user",
            "structured_context": {
                "assistant_decision": "BUY_NOW",
                "prompt_version": "shopping_v1",
            },
        },
        gateway_response={
            "provider": "mock",
            "model": "mock-shopping-explainer",
            "status": "COMPLETED",
            "safety_warnings": [],
            "usage": {"mock": True},
            "metadata": {"prompt_version": "shopping_v1"},
        },
    )

    assert trace["prompt_version"] == "shopping_v1"
