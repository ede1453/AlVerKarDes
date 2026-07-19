from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.products.canonical_service import CanonicalProductService


class CanonicalizationOfferRequest(BaseModel):
    id: str | None = None
    offer_id: str | None = None
    marketplace: str | None = None
    product_name: str
    brand: str | None = None
    model: str | None = None
    variant: str | None = None
    category: str | None = None
    price: str | None = None
    currency: str = "EUR"
    metadata: dict = Field(default_factory=dict)


class CanonicalizationRequest(BaseModel):
    query: str
    offers: list[CanonicalizationOfferRequest] = Field(default_factory=list)


class CachedCanonicalizationRequest(CanonicalizationRequest):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/product-canonicalization", tags=["product-canonicalization"])

# CONNECT-003 (ADR-007 Karar 2): backed by the real products/normalization
# engine (same one the actual ingestion path uses), not the archived
# standalone product_canonicalization domain -- see _arsiv/ for the old
# implementation and WIKI_ROOT 07-Issues-Risks for why it was retired.
_service = CanonicalProductService()
_cache_service = CacheService()
_key_builder = CacheKeyBuilder()


@router.post("/canonicalize")
async def canonicalize_products(
    payload: CanonicalizationRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.canonicalize(payload.model_dump())


@router.post("/canonicalize-cached")
async def canonicalize_products_cached(
    payload: CachedCanonicalizationRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    data = payload.model_dump()
    cache_key = _key_builder.build(
        namespace="product_canonicalization",
        payload={"query": data["query"], "offers": data.get("offers", [])},
    )
    return _cache_service.get_or_set(
        key=cache_key,
        value_factory=lambda: _service.canonicalize(data),
        ttl_seconds=data.get("ttl_seconds", 300),
    )
