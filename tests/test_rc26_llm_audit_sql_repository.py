from datetime import datetime, timezone

import pytest

from app.domains.llm_audit_trace.llm_audit_models import LLMAuditTraceRecord
from app.domains.llm_audit_trace.llm_audit_sql_repository import (
    SQLLLMAuditTraceRepository,
)


class FakeScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return self._rows


class FakeResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def mappings(self):
        return FakeScalarResult(self._rows)


class FakeAsyncDB:
    def __init__(self):
        self.statements = []
        self.params = []
        self.rows = []
        self.committed = False

    async def execute(self, statement, params=None):
        self.statements.append(str(statement))
        self.params.append(params or {})
        return FakeResult(self.rows)

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_sql_llm_audit_repository_save_executes_insert():
    db = FakeAsyncDB()
    repository = SQLLLMAuditTraceRepository(db)

    record = LLMAuditTraceRecord(
        id="11111111-1111-1111-1111-111111111111",
        provider="mock",
        model="mock-shopping-explainer",
        status="COMPLETED",
        assistant_decision="BUY_NOW",
        prompt_hash="a" * 64,
        prompt_version="shopping_v1",
        safety_warnings=[],
        usage={"mock": True},
        metadata={"source": "test"},
        created_at=datetime.now(timezone.utc),
    )

    saved = await repository.save(record)

    assert saved.id == record.id
    assert db.committed is True
    assert "INSERT INTO llm_audit_traces" in db.statements[0]
    assert db.params[0]["prompt_version"] == "shopping_v1"


@pytest.mark.asyncio
async def test_sql_llm_audit_repository_get_maps_row_to_record():
    created_at = datetime.now(timezone.utc)
    db = FakeAsyncDB()
    db.rows = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "provider": "mock",
            "model": "mock-shopping-explainer",
            "status": "COMPLETED",
            "assistant_decision": "BUY_NOW",
            "prompt_hash": "a" * 64,
            "prompt_version": "shopping_v1",
            "safety_warnings": [],
            "usage": {"mock": True},
            "metadata": {"source": "test"},
            "created_at": created_at,
        }
    ]

    record = await SQLLLMAuditTraceRepository(db).get("11111111-1111-1111-1111-111111111111")

    assert record.provider == "mock"
    assert record.prompt_version == "shopping_v1"
    assert record.created_at == created_at
