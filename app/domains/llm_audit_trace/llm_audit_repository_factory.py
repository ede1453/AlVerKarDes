from app.domains.llm_audit_trace.llm_audit_repository import LLMAuditTraceRepository
from app.domains.llm_audit_trace.llm_audit_sql_repository import SQLLLMAuditTraceRepository


class LLMAuditTraceRepositoryFactory:
    def create(self, db=None):
        if db is None:
            return LLMAuditTraceRepository()

        return SQLLLMAuditTraceRepository(db)
