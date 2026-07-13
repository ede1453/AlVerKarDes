from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.product_matching.product_matching_service import ProductMatchingService


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

_service = ProductMatchingService()


@router.post("/match")
async def match_products(payload: ProductMatchingRequest):
    return _service.match(payload.model_dump())


@router.post("/match-cached")
async def match_products_cached(payload: CachedProductMatchingRequest):
    return _service.match_cached(payload.model_dump())
