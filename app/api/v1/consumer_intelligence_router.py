from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.consumer_intelligence.consumer_intelligence_service import (
    ConsumerIntelligenceService,
)
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole


class ConsumerIntelligenceRequest(BaseModel):
    deal_score: int = Field(ge=0, le=100)
    authenticity_score: int = Field(ge=0, le=100)
    recommendation: str
    recommendation_confidence: int = Field(ge=0, le=100)
    trend_direction: str | None = None
    store_trust_score: int | None = Field(default=None, ge=0, le=100)
    stock_status: str | None = None
    reason_codes: list[str] = Field(default_factory=list)


router = APIRouter(prefix="/consumer-intelligence", tags=["consumer-intelligence"])


@router.post("/evaluate")
async def evaluate_consumer_intelligence(
    payload: ConsumerIntelligenceRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return ConsumerIntelligenceService().evaluate(payload.model_dump())
