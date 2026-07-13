from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.user_profiles.user_profile_service import UserProfileService


class UserProfilePreferencesRequest(BaseModel):
    user_id: str
    preferred_marketplaces: list[str] = Field(default_factory=list)
    blocked_marketplaces: list[str] = Field(default_factory=list)
    preferred_brands: list[str] = Field(default_factory=list)
    risk_tolerance: str | None = None


class UserProfileFeedbackMergeRequest(BaseModel):
    user_id: str
    feedback_summary: dict = Field(default_factory=dict)


router = APIRouter(prefix="/user-profiles", tags=["user-profiles"])

_service = UserProfileService()


@router.get("/{user_id}")
async def get_user_profile(user_id: str):
    return _service.get_profile(user_id)


@router.post("/preferences")
async def apply_user_profile_preferences(payload: UserProfilePreferencesRequest):
    return _service.apply_preferences(payload.model_dump())


@router.post("/feedback/merge")
async def merge_user_profile_feedback(payload: UserProfileFeedbackMergeRequest):
    return _service.merge_feedback(payload.model_dump())


@router.get("/{user_id}/recommendation-context")
async def get_user_profile_recommendation_context(user_id: str):
    return _service.recommendation_context(user_id)


@router.post("/clear")
async def clear_user_profiles():
    return _service.clear()
