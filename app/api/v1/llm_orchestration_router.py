from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

try:
    from app.core.database import get_db
except Exception:  # pragma: no cover - compatibility for older app layouts
    get_db = None

from app.domains.llm_audit_trace.llm_audit_service import LLMAuditTraceService
from app.domains.llm_orchestration.guarded_orchestration_service import (
    GuardedLLMOrchestrationService,
)
from app.domains.llm_orchestration.orchestration_service import (
    LLMOrchestrationService,
)


class LLMOrchestrationRunRequest(BaseModel):
    preferred_provider: str = "mock"
    fallback_providers: list[str] = Field(default_factory=lambda: ["mock"])
    model: str = "mock-shopping-explainer"
    system_prompt: str = ""
    user_prompt: str = ""
    guardrails: list[str] = Field(default_factory=list)
    structured_context: dict = Field(default_factory=dict)
    max_attempts: int = Field(default=2, ge=1, le=5)
    prompt_version: str = "shopping_v1"
    timeout_ms: int | None = Field(default=None, ge=1)


class IntelligentLLMOrchestrationRunRequest(LLMOrchestrationRunRequest):
    candidate_providers: list[str] = Field(default_factory=lambda: ["mock", "openai", "local"])
    require_available: bool = True
    max_latency_ms: int | None = Field(default=None, ge=0)


class GuardedLLMOrchestrationRunRequest(LLMOrchestrationRunRequest):
    rate_limit_key: str = "anonymous"
    rate_limit_scope: str = "llm_orchestration"


router = APIRouter(prefix="/llm-orchestration", tags=["llm-orchestration"])


@router.post("/run")
async def run_llm_orchestration(payload: LLMOrchestrationRunRequest):
    return LLMOrchestrationService().run(payload.model_dump())


@router.post("/run-with-audit")
async def run_llm_orchestration_with_audit(payload: LLMOrchestrationRunRequest):
    return await LLMOrchestrationService().run_with_audit(payload.model_dump())


@router.post("/run-intelligent")
async def run_intelligent_llm_orchestration(payload: IntelligentLLMOrchestrationRunRequest):
    return LLMOrchestrationService().run_with_intelligent_selection(payload.model_dump())


@router.post("/run-guarded")
async def run_guarded_llm_orchestration(payload: GuardedLLMOrchestrationRunRequest):
    return GuardedLLMOrchestrationService().run(payload.model_dump())


@router.post("/run-guarded-with-audit")
async def run_guarded_llm_orchestration_with_audit(payload: GuardedLLMOrchestrationRunRequest):
    return await GuardedLLMOrchestrationService().run_with_audit(payload.model_dump())


if get_db is not None:
    @router.post("/run-with-db-audit")
    async def run_llm_orchestration_with_db_audit(
        payload: LLMOrchestrationRunRequest,
        db=Depends(get_db),
    ):
        service = LLMOrchestrationService(
            audit_service=LLMAuditTraceService(db=db)
        )
        return await service.run_with_audit(payload.model_dump())
