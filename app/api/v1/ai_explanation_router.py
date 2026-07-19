from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.ai_explanation.explanation_service import AIExplanationService
from app.domains.identity.dependencies import get_current_user


class AIExplanationRequest(BaseModel):
    language: str = "en"
    tone: str = "clear"
    agent_decision: dict | None = None
    deal_detection: dict | None = None
    discount_intelligence: dict | None = None
    smart_alert: dict | None = None
    price_prediction: dict | None = None
    prompt_version: str = "shopping_explanation_v1"


class CachedAIExplanationRequest(AIExplanationRequest):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/ai-explanation", tags=["ai-explanation"])

_service = AIExplanationService()


@router.post("/explain")
async def explain_decision(
    payload: AIExplanationRequest,
    current_user=Depends(get_current_user),
):
    return _service.explain(payload.model_dump())


@router.post("/explain-cached")
async def explain_decision_cached(
    payload: CachedAIExplanationRequest,
    current_user=Depends(get_current_user),
):
    return _service.explain_cached(payload.model_dump())
