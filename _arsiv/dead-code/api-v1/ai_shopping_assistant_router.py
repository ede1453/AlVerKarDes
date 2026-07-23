from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.ai_shopping_assistant.assistant_service import (
    AIShoppingAssistantService,
)
from app.domains.identity.dependencies import get_current_user


class AIShoppingAssistantAdviceRequest(BaseModel):
    user_id: str | None = None
    query: str | None = None
    product_name: str | None = None
    product_brand: str | None = None
    product_category: str | None = None
    current_price: str | None = None
    currency: str = "EUR"
    final_decision: str = "WATCH"
    confidence: int = Field(default=70, ge=0, le=100)
    risk_level: str | None = None
    opportunity_level: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)
    personalized_decision: str | None = None
    personalized_confidence: int | None = Field(default=None, ge=0, le=100)
    personalization_reasons: list[str] = Field(default_factory=list)
    trust_score: int | None = Field(default=None, ge=0, le=100)
    community_score: int | None = Field(default=None, ge=0, le=100)
    metadata: dict = Field(default_factory=dict)


router = APIRouter(prefix="/ai-shopping-assistant", tags=["ai-shopping-assistant"])


@router.post("/advise")
async def advise(
    payload: AIShoppingAssistantAdviceRequest,
    current_user=Depends(get_current_user),
):
    return AIShoppingAssistantService().advise(payload.model_dump())
