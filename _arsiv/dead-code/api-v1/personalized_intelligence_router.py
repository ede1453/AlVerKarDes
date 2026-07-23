from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.domains.identity.dependencies import ensure_owner, get_current_user
from app.domains.personalized_intelligence.personalized_intelligence_service import (
    PersonalizedIntelligenceService,
)


class UserPreferenceProfileRequest(BaseModel):
    user_id: str
    preferred_brands: list[str] = Field(default_factory=list)
    avoided_brands: list[str] = Field(default_factory=list)
    preferred_categories: list[str] = Field(default_factory=list)
    price_sensitivity: str = "MEDIUM"
    minimum_confidence: int = Field(default=70, ge=0, le=100)


class PersonalizeDecisionRequest(BaseModel):
    user_id: str
    final_decision: str
    confidence: int = Field(ge=0, le=100)
    product_brand: str | None = None
    product_category: str | None = None
    current_price: str | None = None
    risk_level: str | None = None
    opportunity_level: str | None = None
    reason_codes: list[str] = Field(default_factory=list)


router = APIRouter(prefix="/personalized-intelligence", tags=["personalized-intelligence"])

_service = PersonalizedIntelligenceService()


@router.post("/profiles")
async def save_user_preference_profile(
    payload: UserPreferenceProfileRequest,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)
    return await _service.save_profile(payload.model_dump())


@router.get("/profiles/{user_id}")
async def get_user_preference_profile(
    user_id: str,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    result = await _service.get_profile(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="user_preference_profile_not_found")
    return result


@router.post("/decisions/personalize")
async def personalize_decision(
    payload: PersonalizeDecisionRequest,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)
    return await _service.personalize_decision(payload.model_dump())
