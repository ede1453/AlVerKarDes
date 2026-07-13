from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.trust_intelligence.trust_service import TrustIntelligenceService


class TrustSignalRequest(BaseModel):
    source_type: str
    source_id: str
    positive_count: int = Field(default=0, ge=0)
    negative_count: int = Field(default=0, ge=0)
    neutral_count: int = Field(default=0, ge=0)
    fraud_count: int = Field(default=0, ge=0)
    return_count: int = Field(default=0, ge=0)
    total_count: int = Field(default=0, ge=0)


class TrustEvaluationRequest(BaseModel):
    decision_id: str | None = None
    user_id: str | None = None
    store_id: str | None = None
    product_id: str | None = None
    community_id: str = "global"
    base_confidence: int = Field(default=70, ge=0, le=100)
    final_decision: str = "WATCH"
    feedback_summary: dict = Field(default_factory=dict)


router = APIRouter(prefix="/trust-intelligence", tags=["trust-intelligence"])

_service = TrustIntelligenceService()


@router.post("/signals")
async def upsert_trust_signal(payload: TrustSignalRequest):
    return await _service.upsert_signal(payload.model_dump())


@router.get("/profiles/{entity_type}/{entity_id}")
async def get_trust_profile(entity_type: str, entity_id: str):
    result = await _service.get_profile(entity_type, entity_id)
    if result is None:
        raise HTTPException(status_code=404, detail="trust_profile_not_found")
    return result


@router.post("/evaluate")
async def evaluate_trust(payload: TrustEvaluationRequest):
    return await _service.evaluate(payload.model_dump())
