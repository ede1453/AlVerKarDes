from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.discount_intelligence.discount_service import DiscountIntelligenceService
from app.domains.identity.dependencies import get_current_user


class DiscountAnalyzeRequest(BaseModel):
    product_key: str
    current_price: str | None = None
    claimed_original_price: str | None = None
    price_history: dict | None = None
    deal_detection: dict | None = None
    price_prediction: dict | None = None


class CachedDiscountAnalyzeRequest(DiscountAnalyzeRequest):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/discount-intelligence", tags=["discount-intelligence"])

_service = DiscountIntelligenceService()


@router.post("/analyze")
async def analyze_discount(
    payload: DiscountAnalyzeRequest,
    current_user=Depends(get_current_user),
):
    return _service.analyze(payload.model_dump())


@router.post("/analyze-cached")
async def analyze_discount_cached(
    payload: CachedDiscountAnalyzeRequest,
    current_user=Depends(get_current_user),
):
    return _service.analyze_cached(payload.model_dump())
