from app.domains.llm_audit_trace.llm_audit_repository import LLMAuditTraceRepository
from app.domains.llm_audit_trace.llm_audit_repository_factory import (
    LLMAuditTraceRepositoryFactory,
)
from app.domains.llm_audit_trace.llm_audit_sql_repository import (
    SQLLLMAuditTraceRepository,
)


class DummyDB:
    pass


def test_llm_audit_repository_factory_returns_in_memory_without_db():
    repository = LLMAuditTraceRepositoryFactory().create()

    assert isinstance(repository, LLMAuditTraceRepository)


def test_llm_audit_repository_factory_returns_sql_repository_with_db():
    repository = LLMAuditTraceRepositoryFactory().create(DummyDB())

    assert isinstance(repository, SQLLLMAuditTraceRepository)
