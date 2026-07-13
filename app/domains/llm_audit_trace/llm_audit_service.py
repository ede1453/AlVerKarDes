from app.domains.llm_audit_trace.llm_audit_models import (
    LLMAuditTraceCreate,
    create_llm_audit_trace_record,
)
from app.domains.llm_audit_trace.llm_audit_repository import LLMAuditTraceRepository
from app.domains.llm_audit_trace.llm_audit_repository_factory import (
    LLMAuditTraceRepositoryFactory,
)
from app.domains.llm_audit_trace.llm_audit_serializer import serialize_llm_audit_trace
from app.domains.llm_audit_trace.prompt_hashing import PromptHasher


class LLMAuditTraceService:
    def __init__(
        self,
        repository: LLMAuditTraceRepository | None = None,
        prompt_hasher: PromptHasher | None = None,
        db=None,
        repository_factory: LLMAuditTraceRepositoryFactory | None = None,
    ):
        self.repository = repository or (repository_factory or LLMAuditTraceRepositoryFactory()).create(db)
        self.prompt_hasher = prompt_hasher or PromptHasher()

    async def create_from_gateway_payload(self, *, request_payload: dict, gateway_response: dict):
        structured_context = request_payload.get("structured_context", {})
        prompt_version = (
            request_payload.get("prompt_version")
            or structured_context.get("prompt_version")
            or gateway_response.get("metadata", {}).get("prompt_version")
            or "shopping_v1"
        )

        prompt_hash = self.prompt_hasher.hash_prompt(
            system_prompt=request_payload.get("system_prompt", ""),
            user_prompt=request_payload.get("user_prompt", ""),
            structured_context=structured_context,
        )

        record = create_llm_audit_trace_record(
            LLMAuditTraceCreate(
                provider=gateway_response.get("provider", request_payload.get("provider", "unknown")),
                model=gateway_response.get("model", request_payload.get("model", "unknown")),
                status=gateway_response.get("status", "UNKNOWN"),
                assistant_decision=structured_context.get("assistant_decision"),
                prompt_hash=prompt_hash,
                prompt_version=prompt_version,
                safety_warnings=gateway_response.get("safety_warnings", []),
                usage=gateway_response.get("usage", {}),
                metadata={
                    "gateway_metadata": gateway_response.get("metadata", {}),
                    "request_provider": request_payload.get("provider"),
                },
            )
        )

        saved = await self.repository.save(record)
        return serialize_llm_audit_trace(saved)

    async def get(self, trace_id: str):
        record = await self.repository.get(trace_id)
        if record is None:
            return None
        return serialize_llm_audit_trace(record)

    async def list_recent(self, limit: int = 20):
        records = await self.repository.list_recent(limit=limit)
        return [serialize_llm_audit_trace(record) for record in records]
