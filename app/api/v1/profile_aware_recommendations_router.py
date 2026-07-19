from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.identity.dependencies import ensure_owner, get_current_user
from app.domains.profile_aware_recommendations.profile_aware_service import (
    ProfileAwareRecommendationService,
)


class ProfileAwareRecommendationRequest(BaseModel):
    user_id: str
    query: str
    candidates: list[dict] = Field(default_factory=list)
    profile_context: dict | None = None
    personalization: dict | None = None
    discount_intelligence: dict | None = None
    deal_detection: dict | None = None
    price_prediction: dict | None = None


router = APIRouter(prefix="/profile-aware-recommendations", tags=["profile-aware-recommendations"])

_service = ProfileAwareRecommendationService()


@router.post("/recommend")
async def recommend_with_profile(
    payload: ProfileAwareRecommendationRequest,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)
    return _service.recommend(payload.model_dump())
