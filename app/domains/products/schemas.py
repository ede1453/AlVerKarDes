from uuid import UUID

from pydantic import BaseModel, Field


class BrandCreate(BaseModel):
    name: str
    slug: str
    website: str | None = None
    country: str | None = None
    trust_score: float | None = Field(default=None, ge=0, le=100)


class CategoryCreate(BaseModel):
    name: str
    slug: str
    parent_id: UUID | None = None
    description: str | None = None


class ProductCreate(BaseModel):
    title: str
    brand_id: UUID | None = None
    category_id: UUID | None = None
    model_number: str | None = None
    gtin: str | None = None
    manufacturer_sku: str | None = None
    canonical_key: str | None = None
    description: str | None = None
    metadata: dict = Field(default_factory=dict)
