from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.user_activity.activity_service import UserActivityService


class UserActivityRecordRequest(BaseModel):
    user_id: str
    event_type: str
    product_key: str | None = None
    recommendation_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class RecommendationAdjustmentRequest(BaseModel):
    user_id: str
    recommendations: list[dict] = Field(default_factory=list)


router = APIRouter(prefix="/user-activity", tags=["user-activity"])

_service = UserActivityService()


@router.post("/record")
async def record_user_activity(payload: UserActivityRecordRequest):
    return _service.record(payload.model_dump())


@router.get("/users/{user_id}/events")
async def list_user_activity_events(user_id: str):
    return _service.list_for_user(user_id)


@router.get("/users/{user_id}/summary")
async def summarize_user_activity(user_id: str):
    return _service.summarize(user_id)


@router.post("/recommendations/adjust")
async def adjust_recommendations_from_activity(payload: RecommendationAdjustmentRequest):
    return _service.adjust_recommendations(payload.model_dump())


@router.post("/clear")
async def clear_user_activity():
    return _service.clear()
