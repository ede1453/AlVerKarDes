
from sqlalchemy import text

from app.domains.llm_audit_trace.llm_audit_models import (
    LLMAuditTraceRecord,
)


class SQLLLMAuditTraceRepository:
    """PostgreSQL-backed LLM audit trace repository.

    This implementation intentionally uses SQLAlchemy text statements instead of
    introducing a new ORM model layer. That keeps it compatible with the existing
    Alembic-created table and avoids changing previous in-memory test contracts.
    """

    def __init__(self, db):
        self.db = db

    async def save(self, record: LLMAuditTraceRecord):
        await self.db.execute(
            text(
                """
                INSERT INTO llm_audit_traces (
                    id,
                    provider,
                    model,
                    status,
                    assistant_decision,
                    prompt_hash,
                    prompt_version,
                    safety_warnings,
                    usage,
                    metadata,
                    created_at
                )
                VALUES (
                    :id,
                    :provider,
                    :model,
                    :status,
                    :assistant_decision,
                    :prompt_hash,
                    :prompt_version,
                    CAST(:safety_warnings AS JSONB),
                    CAST(:usage AS JSONB),
                    CAST(:metadata AS JSONB),
                    :created_at
                )
                """
            ),
            {
                "id": str(record.id),
                "provider": record.provider,
                "model": record.model,
                "status": record.status,
                "assistant_decision": record.assistant_decision,
                "prompt_hash": record.prompt_hash,
                "prompt_version": record.prompt_version,
                "safety_warnings": self._json(record.safety_warnings),
                "usage": self._json(record.usage),
                "metadata": self._json(record.metadata),
                "created_at": record.created_at,
            },
        )

        await self._commit_if_supported()
        return record

    async def get(self, trace_id: str):
        result = await self.db.execute(
            text(
                """
                SELECT
                    id,
                    provider,
                    model,
                    status,
                    assistant_decision,
                    prompt_hash,
                    prompt_version,
                    safety_warnings,
                    usage,
                    metadata,
                    created_at
                FROM llm_audit_traces
                WHERE id = :id
                """
            ),
            {"id": str(trace_id)},
        )

        row = result.mappings().first()
        if row is None:
            return None

        return self._row_to_record(row)

    async def list_recent(self, limit: int = 20):
        result = await self.db.execute(
            text(
                """
                SELECT
                    id,
                    provider,
                    model,
                    status,
                    assistant_decision,
                    prompt_hash,
                    prompt_version,
                    safety_warnings,
                    usage,
                    metadata,
                    created_at
                FROM llm_audit_traces
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": int(limit)},
        )

        return [
            self._row_to_record(row)
            for row in result.mappings().all()
        ]

    def _row_to_record(self, row):
        return LLMAuditTraceRecord(
            id=str(row["id"]),
            provider=row["provider"],
            model=row["model"],
            status=row["status"],
            assistant_decision=row["assistant_decision"],
            prompt_hash=row["prompt_hash"],
            prompt_version=row["prompt_version"],
            safety_warnings=list(row["safety_warnings"] or []),
            usage=dict(row["usage"] or {}),
            metadata=dict(row["metadata"] or {}),
            created_at=row["created_at"],
        )

    async def _commit_if_supported(self):
        commit = getattr(self.db, "commit", None)
        if commit is not None:
            result = commit()
            if hasattr(result, "__await__"):
                await result

    def _json(self, value):
        import json

        return json.dumps(value, ensure_ascii=False, default=str)
