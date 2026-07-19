from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.marketplace_aggregation.marketplace_service import (
    MarketplaceAggregationService,
)


class MarketplaceOfferRequest(BaseModel):
    marketplace: str
    seller: str | None = None
    product_name: str
    price: float | str
    currency: str = "EUR"
    url: str | None = None
    availability: str = "UNKNOWN"
    metadata: dict = Field(default_factory=dict)


class MarketplaceAggregationRequest(BaseModel):
    query: str
    offers: list[MarketplaceOfferRequest] = Field(default_factory=list)


class CachedMarketplaceAggregationRequest(MarketplaceAggregationRequest):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/marketplace-aggregation", tags=["marketplace-aggregation"])
_service = MarketplaceAggregationService()


@router.post("/aggregate")
async def aggregate_marketplace_offers(payload: MarketplaceAggregationRequest):
    return _service.aggregate(payload.model_dump())


@router.post("/aggregate-cached")
async def aggregate_marketplace_offers_cached(payload: CachedMarketplaceAggregationRequest):
    return _service.aggregate_cached(payload.model_dump())
