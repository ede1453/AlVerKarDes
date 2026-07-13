from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.decision_memory.decision_memory_service import DecisionMemoryService


class DecisionMemoryStoreRequest(BaseModel):
    product_id: str | None = None
    offer_id: str | None = None
    country: str = "DE"
    final_decision: str
    confidence: int = Field(ge=0, le=100)
    risk_level: str | None = None
    opportunity_level: str | None = None
    deal_score: int | None = Field(default=None, ge=0, le=100)
    authenticity_score: int | None = Field(default=None, ge=0, le=100)
    recommendation: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    decision_context: dict = Field(default_factory=dict)


class DecisionOutcomeRequest(BaseModel):
    decision_price: str
    future_price: str


router = APIRouter(prefix="/decision-memory", tags=["decision-memory"])

_service = DecisionMemoryService()


@router.post("/store")
async def store_decision_memory(payload: DecisionMemoryStoreRequest):
    return await _service.store(payload.model_dump())


@router.get("/{decision_id}")
async def get_decision_memory(decision_id: str):
    result = await _service.get(decision_id)
    if result is None:
        raise HTTPException(status_code=404, detail="decision_memory_not_found")
    return result


@router.post("/{decision_id}/outcome")
async def evaluate_decision_outcome(decision_id: str, payload: DecisionOutcomeRequest):
    result = await _service.evaluate_outcome(decision_id, payload.model_dump())
    if result is None:
        raise HTTPException(status_code=404, detail="decision_memory_not_found")
    return result
