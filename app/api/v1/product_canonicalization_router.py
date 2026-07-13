from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.product_canonicalization.canonical_service import (
    ProductCanonicalizationService,
)


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

_service = ProductCanonicalizationService()


@router.post("/canonicalize")
async def canonicalize_products(payload: CanonicalizationRequest):
    return _service.canonicalize(payload.model_dump())


@router.post("/canonicalize-cached")
async def canonicalize_products_cached(payload: CachedCanonicalizationRequest):
    return _service.canonicalize_cached(payload.model_dump())
