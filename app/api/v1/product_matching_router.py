from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.products.matching_engine import ProductMatchEngine


class ProductMatchOfferRequest(BaseModel):
    id: str | None = None
    offer_id: str | None = None
    marketplace: str
    product_name: str
    price: str
    currency: str = "EUR"
    metadata: dict = Field(default_factory=dict)


class ProductMatchingRequest(BaseModel):
    query: str
    offers: list[ProductMatchOfferRequest] = Field(default_factory=list)


class CachedProductMatchingRequest(ProductMatchingRequest):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/product-matching", tags=["product-matching"])

# CONNECT-003 (ADR-007 Karar 2): backed by the real products/matching_engine
# (same identity engine the actual ingestion path uses), not the archived
# standalone product_matching domain -- see _arsiv/ for the old
# implementation and WIKI_ROOT 07-Issues-Risks for why it was retired.
_service = ProductMatchEngine()
_cache_service = CacheService()
_key_builder = CacheKeyBuilder()


@router.post("/match")
async def match_products(
    payload: ProductMatchingRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.match(payload.model_dump())


@router.post("/match-cached")
async def match_products_cached(
    payload: CachedProductMatchingRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    data = payload.model_dump()
    cache_key = _key_builder.build(
        namespace="product_matching",
        payload={"query": data["query"], "offers": data.get("offers", [])},
    )
    return _cache_service.get_or_set(
        key=cache_key,
        value_factory=lambda: _service.match(data),
        ttl_seconds=data.get("ttl_seconds", 300),
    )
