from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.decision_context.decision_context_service import DecisionContextService
from app.domains.identity.dependencies import get_current_user


class DecisionContextRequest(BaseModel):
    product_id: str | None = None
    offer_id: str | None = None
    country: str = "DE"
    currency: str = "EUR"
    deal_score: int | None = Field(default=None, ge=0, le=100)
    authenticity_score: int | None = Field(default=None, ge=0, le=100)
    recommendation: str | None = None
    recommendation_confidence: int | None = Field(default=None, ge=0, le=100)
    final_decision: str | None = None
    risk_level: str | None = None
    opportunity_level: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


router = APIRouter(prefix="/decision-context", tags=["decision-context"])


@router.post("/build")
async def build_decision_context(
    payload: DecisionContextRequest,
    current_user=Depends(get_current_user),
):
    return DecisionContextService().build(payload.model_dump())
