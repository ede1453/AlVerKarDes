from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.explainability.explanation_service import ExplanationService


class ExplanationRequest(BaseModel):
    final_decision: str
    confidence: int = Field(ge=0, le=100)
    risk_level: str | None = None
    opportunity_level: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)
    scores: dict = Field(default_factory=dict)
    market: dict = Field(default_factory=dict)


router = APIRouter(prefix="/explanations", tags=["explanations"])


@router.post("/generate")
async def generate_explanation(payload: ExplanationRequest):
    return ExplanationService().explain(payload.model_dump())
