from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.decision_memory.decision_memory_repository import DecisionMemoryRepository
from app.domains.decision_memory.decision_memory_service import DecisionMemoryService
from app.domains.identity.dependencies import ensure_owner, get_current_user


class DecisionMemoryStoreRequest(BaseModel):
    user_id: str
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


@router.post("/store")
async def store_decision_memory(
    payload: DecisionMemoryStoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)
    service = DecisionMemoryService(repository=DecisionMemoryRepository(db))
    return await service.store(payload.model_dump())


@router.get("/{decision_id}")
async def get_decision_memory(
    decision_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = DecisionMemoryService(repository=DecisionMemoryRepository(db))
    result = await service.get(decision_id)
    if result is None:
        raise HTTPException(status_code=404, detail="decision_memory_not_found")
    ensure_owner(current_user, result["user_id"])
    return result


@router.post("/{decision_id}/outcome")
async def evaluate_decision_outcome(
    decision_id: str,
    payload: DecisionOutcomeRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = DecisionMemoryService(repository=DecisionMemoryRepository(db))
    existing = await service.get(decision_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="decision_memory_not_found")
    ensure_owner(current_user, existing["user_id"])

    result = await service.evaluate_outcome(decision_id, payload.model_dump())
    if result is None:
        raise HTTPException(status_code=404, detail="decision_memory_not_found")
    return result
