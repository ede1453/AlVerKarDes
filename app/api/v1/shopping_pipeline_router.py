from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.shopping_pipeline.pipeline_service import ShoppingPipelineService


class ShoppingPipelineRequest(BaseModel):
    user_id: str
    query: str
    offers: list[dict] = Field(default_factory=list)
    profile_context: dict | None = None
    personalization: dict | None = None
    price_history: dict | None = None
    claimed_original_price: str | None = None
    prediction_horizon_days: int = 7
    channels: list[str] = Field(default_factory=lambda: ["in_app"])
    deliver_notification: bool = False
    notification_provider: str = "mock"
    language: str = "en"
    tone: str = "clear"


router = APIRouter(prefix="/shopping-pipeline", tags=["shopping-pipeline"])

_service = ShoppingPipelineService()


@router.post("/run")
async def run_shopping_pipeline(payload: ShoppingPipelineRequest):
    return _service.run(payload.model_dump())
