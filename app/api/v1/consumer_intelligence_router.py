from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.consumer_intelligence.consumer_intelligence_service import (
    ConsumerIntelligenceService,
)


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
async def evaluate_consumer_intelligence(payload: ConsumerIntelligenceRequest):
    return ConsumerIntelligenceService().evaluate(payload.model_dump())
