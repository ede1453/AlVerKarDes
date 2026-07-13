from datetime import datetime

from pydantic import BaseModel, Field


class FeedItem(BaseModel):
    store_slug: str
    product_title: str
    product_url: str
    price: float = Field(ge=0)
    currency: str = "EUR"
    original_price: float | None = Field(default=None, ge=0)
    shipping_price: float | None = Field(default=None, ge=0)
    stock_status: str | None = None
    brand: str | None = None
    gtin: str | None = None
    sku: str | None = None
    observed_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class FeedImportResult(BaseModel):
    total_items: int
    imported_items: int
    skipped_items: int
    errors: list[dict] = Field(default_factory=list)
