from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.llm_explanation_adapter.llm_explanation_service import (
    LLMExplanationAdapterService,
)


class LLMExplanationPrepareRequest(BaseModel):
    assistant_decision: str
    headline: str
    summary: str
    confidence: int = Field(ge=0, le=100)
    risk_level: str | None = None
    opportunity_level: str | None = None
    next_actions: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)
    assistant_context: dict = Field(default_factory=dict)
    language: str = "en"
    tone: str = "clear"
    prompt_version: str = "shopping_v1"


router = APIRouter(prefix="/llm-explanations", tags=["llm-explanations"])


@router.post("/prepare")
async def prepare_llm_explanation(payload: LLMExplanationPrepareRequest):
    return LLMExplanationAdapterService().prepare(payload.model_dump())
