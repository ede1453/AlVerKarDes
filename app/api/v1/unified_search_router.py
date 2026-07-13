from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.unified_search.unified_search_service import UnifiedSearchService


class UnifiedSearchOfferRequest(BaseModel):
    marketplace: str
    seller: str | None = None
    product_name: str
    price: str
    currency: str = "EUR"
    url: str | None = None
    availability: str = "UNKNOWN"
    metadata: dict = Field(default_factory=dict)


class UnifiedSearchRequestModel(BaseModel):
    query: str
    user_id: str | None = None
    marketplaces: list[str] = Field(default_factory=list)
    offers: list[UnifiedSearchOfferRequest] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class CachedUnifiedSearchRequestModel(UnifiedSearchRequestModel):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/unified-search", tags=["unified-search"])

_service = UnifiedSearchService()


@router.post("/search")
async def unified_search(payload: UnifiedSearchRequestModel):
    return _service.search(payload.model_dump())


@router.post("/search-cached")
async def unified_search_cached(payload: CachedUnifiedSearchRequestModel):
    return _service.search_cached(payload.model_dump())
