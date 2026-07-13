from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.feedback_learning.feedback_service import FeedbackLearningService


class FeedbackSubmitRequest(BaseModel):
    user_id: str
    decision_id: str | None = None
    product_id: str | None = None
    offer_id: str | None = None
    feedback_type: str = "HELPFUL"
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None
    metadata: dict = Field(default_factory=dict)


router = APIRouter(prefix="/feedback-learning", tags=["feedback-learning"])

_service = FeedbackLearningService()


@router.post("/feedback")
async def submit_feedback(payload: FeedbackSubmitRequest):
    return await _service.submit_feedback(payload.model_dump())


@router.get("/feedback/{feedback_id}")
async def get_feedback(feedback_id: str):
    result = await _service.get_feedback(feedback_id)
    if result is None:
        raise HTTPException(status_code=404, detail="feedback_not_found")
    return result


@router.get("/users/{user_id}/summary")
async def summarize_user_feedback(user_id: str):
    return await _service.summarize_user_feedback(user_id)


@router.get("/decisions/{decision_id}/summary")
async def summarize_decision_feedback(decision_id: str):
    return await _service.summarize_decision_feedback(decision_id)
