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
    # VISION-000 (ADR-018): decision_memory writes are keyed to the token-
    # verified current_user.id, never to the request body's `user_id` field
    # (which is caller-supplied and not cross-checked against current_user
    # elsewhere in this endpoint) -- avoids attributing a stored decision to
    # a spoofed/arbitrary user_id.
    return await _service.run(payload.model_dump(), db, authenticated_user_id=str(current_user.id))
