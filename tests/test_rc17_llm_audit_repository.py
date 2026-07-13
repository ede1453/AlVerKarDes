import pytest

from app.domains.llm_audit_trace.llm_audit_models import (
    LLMAuditTraceCreate,
    create_llm_audit_trace_record,
)
from app.domains.llm_audit_trace.llm_audit_repository import InMemoryLLMAuditTraceRepository


@pytest.mark.asyncio
async def test_llm_audit_repository_saves_and_reads_trace():
    repo = InMemoryLLMAuditTraceRepository()
    record = create_llm_audit_trace_record(
        LLMAuditTraceCreate(provider="mock", model="mock", status="COMPLETED")
    )

    saved = await repo.save(record)
    found = await repo.get(saved.id)

    assert found.id == saved.id
    assert found.status == "COMPLETED"
