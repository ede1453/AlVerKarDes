from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.decision_pipeline.ai_decision_pipeline_service import (
    AIDecisionPipelineService,
)
from app.domains.identity.dependencies import get_current_user


class AIDecisionPipelineRequest(BaseModel):
    deal_score: int = Field(ge=0, le=100)
    authenticity_score: int = Field(ge=0, le=100)
    recommendation: str
    recommendation_confidence: int = Field(ge=0, le=100)
    trend_direction: str | None = None
    store_trust_score: int | None = Field(default=None, ge=0, le=100)
    stock_status: str | None = None
    reason_codes: list[str] = Field(default_factory=list)


router = APIRouter(prefix="/ai-decision-pipeline", tags=["ai-decision-pipeline"])


@router.post("/run")
async def run_ai_decision_pipeline(
    payload: AIDecisionPipelineRequest,
    current_user=Depends(get_current_user),
):
    return AIDecisionPipelineService().run(payload.model_dump())
