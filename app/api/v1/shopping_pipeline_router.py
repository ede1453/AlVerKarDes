from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.shopping_pipeline.pipeline_service import ShoppingPipelineService
from app.domains.identity.dependencies import get_current_user


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
async def run_shopping_pipeline(
    payload: ShoppingPipelineRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _service.run(payload.model_dump(), db)
