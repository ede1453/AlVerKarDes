from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StoreCreate(BaseModel):
    name: str
    slug: str
    website: str | None = None
    country: str = "DE"
    affiliate_enabled: bool = False
    affiliate_network: str | None = None
    trust_score: float | None = Field(default=None, ge=0, le=100)


class OfferCreate(BaseModel):
    product_id: UUID
    variant_id: UUID | None = None
    store_id: UUID
    url: str
    store_sku: str | None = None
    title_on_store: str | None = None


class PriceSnapshotCreate(BaseModel):
    offer_id: UUID
    amount: float = Field(ge=0)
    currency: str = "EUR"
    original_amount: float | None = Field(default=None, ge=0)
    shipping_amount: float | None = Field(default=None, ge=0)
    stock_status: str | None = None
    source: str | None = None
    observed_at: datetime | None = None
    is_real_data: bool = True
