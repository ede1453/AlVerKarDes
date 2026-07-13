import pytest

from app.domains.llm_audit_trace.llm_audit_repository import InMemoryLLMAuditTraceRepository
from app.domains.llm_audit_trace.llm_audit_service import LLMAuditTraceService


@pytest.mark.asyncio
async def test_llm_audit_service_creates_trace_from_gateway_payload():
    service = LLMAuditTraceService(repository=InMemoryLLMAuditTraceRepository())

    trace = await service.create_from_gateway_payload(
        request_payload={
            "provider": "mock",
            "model": "mock-shopping-explainer",
            "system_prompt": "system",
            "user_prompt": "user",
            "structured_context": {"assistant_decision": "BUY_NOW"},
        },
        gateway_response={
            "provider": "mock",
            "model": "mock-shopping-explainer",
            "status": "COMPLETED",
            "safety_warnings": [],
            "usage": {"mock": True},
            "metadata": {"deterministic": True},
        },
    )

    assert trace["provider"] == "mock"
    assert trace["assistant_decision"] == "BUY_NOW"
    assert len(trace["prompt_hash"]) == 64
