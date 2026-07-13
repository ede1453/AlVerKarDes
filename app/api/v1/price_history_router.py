from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.price_history.price_history_service import PriceHistoryService


class PricePointRequest(BaseModel):
    product_key: str
    marketplace: str = "unknown"
    price: str
    currency: str = "EUR"
    metadata: dict = Field(default_factory=dict)


class PriceHistoryBulkAddRequest(BaseModel):
    points: list[PricePointRequest] = Field(default_factory=list)


class PriceHistoryCachedSummaryRequest(BaseModel):
    product_key: str
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/price-history", tags=["price-history"])

_service = PriceHistoryService()


@router.post("/points")
async def add_price_point(payload: PricePointRequest):
    return _service.add_point(payload.model_dump())


@router.post("/points/bulk")
async def bulk_add_price_points(payload: PriceHistoryBulkAddRequest):
    return _service.bulk_add({"points": [point.model_dump() for point in payload.points]})


@router.get("/{product_key}/summary")
async def get_price_history_summary(product_key: str):
    return _service.summary(product_key)


@router.post("/summary-cached")
async def get_price_history_summary_cached(payload: PriceHistoryCachedSummaryRequest):
    return _service.summary_cached(payload.model_dump())


@router.post("/clear")
async def clear_price_history():
    return _service.clear()
