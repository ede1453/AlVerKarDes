from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class LLMAuditTraceCreate:
    provider: str
    model: str
    status: str
    assistant_decision: str | None = None
    prompt_hash: str | None = None
    prompt_version: str = "shopping_v1"
    safety_warnings: list[str] = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class LLMAuditTraceRecord:
    id: str
    provider: str
    model: str
    status: str
    assistant_decision: str | None
    prompt_hash: str | None
    prompt_version: str
    safety_warnings: list[str]
    usage: dict
    metadata: dict
    created_at: datetime


def create_llm_audit_trace_record(data: LLMAuditTraceCreate) -> LLMAuditTraceRecord:
    return LLMAuditTraceRecord(
        id=str(uuid4()),
        provider=data.provider,
        model=data.model,
        status=data.status,
        assistant_decision=data.assistant_decision,
        prompt_hash=data.prompt_hash,
        prompt_version=data.prompt_version,
        safety_warnings=list(data.safety_warnings),
        usage=dict(data.usage),
        metadata=dict(data.metadata),
        created_at=datetime.now(timezone.utc),
    )
