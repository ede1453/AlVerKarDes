from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.identity.dependencies import ensure_owner, get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.user_profiles.user_profile_repository import UserProfileDBRepository
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


def _service(db: AsyncSession) -> UserProfileService:
    # SCALE-008: Postgres-backed now (UserProfileDBRepository) -- same
    # per-request construction pattern as job_queue_router.py's
    # _service(db) helper (SCALE-003). No more module-level singleton: a
    # shared instance can't hold a request-scoped AsyncSession, and
    # get_or_create_for_update()'s SELECT FOR UPDATE needs a real
    # transaction per request anyway.
    return UserProfileService(repository=UserProfileDBRepository(db))


@router.get("/{user_id}")
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return await _service(db).get_profile(user_id)


@router.post("/preferences")
async def apply_user_profile_preferences(
    payload: UserProfilePreferencesRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)
    return await _service(db).apply_preferences(payload.model_dump())


@router.post("/feedback/merge")
async def merge_user_profile_feedback(
    payload: UserProfileFeedbackMergeRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)
    return await _service(db).merge_feedback(payload.model_dump())


@router.get("/{user_id}/recommendation-context")
async def get_user_profile_recommendation_context(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return await _service(db).recommendation_context(user_id)


@router.post("/clear")
async def clear_user_profiles(
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return await _service(db).clear()
