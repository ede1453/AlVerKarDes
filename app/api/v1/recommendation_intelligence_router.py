from fastapi import APIRouter
from pydantic import BaseModel

from app.domains.analytics.recommendation_intelligence_engine import (
    RecommendationIntelligenceEngine,
    RecommendationIntelligenceInput,
)
from app.domains.analytics.recommendation_intelligence_serializer import (
    serialize_recommendation_intelligence,
)


class RecommendationIntelligenceRequest(BaseModel):
    deal_score: int
    authenticity_score: int
    trend_direction: str | None = None
    store_trust_score: int | None = None
    stock_status: str | None = None


router = APIRouter(prefix="/recommendations/intelligence", tags=["recommendations"])


@router.post("/evaluate")
async def evaluate_recommendation_intelligence(payload: RecommendationIntelligenceRequest):
    result = RecommendationIntelligenceEngine().evaluate(
        RecommendationIntelligenceInput(
            deal_score=payload.deal_score,
            authenticity_score=payload.authenticity_score,
            trend_direction=payload.trend_direction,
            store_trust_score=payload.store_trust_score,
            stock_status=payload.stock_status,
        )
    )

    return serialize_recommendation_intelligence(result)
