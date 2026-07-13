from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.deal_detection.deal_detection_service import DealDetectionService


class DealDetectionRequest(BaseModel):
    product_key: str
    offer: dict = Field(default_factory=dict)
    price_history: dict | None = None
    personalization: dict | None = None


class CachedDealDetectionRequest(DealDetectionRequest):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/deal-detection", tags=["deal-detection"])

_service = DealDetectionService()


@router.post("/detect")
async def detect_deal(payload: DealDetectionRequest):
    return _service.detect(payload.model_dump())


@router.post("/detect-cached")
async def detect_deal_cached(payload: CachedDealDetectionRequest):
    return _service.detect_cached(payload.model_dump())
