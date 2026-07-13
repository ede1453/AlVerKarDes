import pytest

from app.domains.llm_audit_trace.llm_audit_service import LLMAuditTraceService


class FakeRepository:
    def __init__(self):
        self.saved = None

    async def save(self, record):
        self.saved = record
        return record

    async def get(self, trace_id):
        return self.saved

    async def list_recent(self, limit=20):
        return [self.saved] if self.saved is not None else []


@pytest.mark.asyncio
async def test_llm_audit_service_still_accepts_repository_injection():
    repository = FakeRepository()
    service = LLMAuditTraceService(repository=repository)

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

    assert trace["provider"] == "mock"
    assert trace["prompt_version"] == "shopping_v1"
    assert repository.saved is not None
