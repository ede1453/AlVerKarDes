from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.recommendations.recommendation_service import RecommendationService


class RecommendationRequest(BaseModel):
    query: str
    user_id: str | None = None
    candidates: list[dict] = Field(default_factory=list)
    personalization: dict | None = None
    discount_intelligence: dict | None = None
    deal_detection: dict | None = None
    price_prediction: dict | None = None


class CachedRecommendationRequest(RecommendationRequest):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/recommendations", tags=["recommendations"])

_service = RecommendationService()

_compat_sessions: dict[str, dict] = {}

@router.post("/recommend")
async def recommend_products(payload: RecommendationRequest):
    return _service.recommend(payload.model_dump())


@router.post("/recommend-cached")
async def recommend_products_cached(payload: CachedRecommendationRequest):
    return _service.recommend_cached(payload.model_dump())

@router.post("/analyze")
async def analyze_product(payload: RecommendationRequest):
    result = _service.recommend(payload.model_dump())
    _compat_sessions[result["run_id"]] = result
    return result

@router.get("/sessions/{session_id}")
async def get_session_recommendations(session_id: str):
    session = _compat_sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="recommendation_session_not_found")
    return session