from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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
    # Required, not optional: every product row must be born with a real
    # canonical_key, no exceptions -- a product created without one can
    # never be found by watchlist/deal-feed/price-history matching, which
    # all key off canonical_key (found live: "Test Product AUTH003P2",
    # created with canonical_key=None, broke "Add to watchlist" with a
    # 422). Callers that don't know their canonical_key upfront should go
    # through ProductService.get_or_create_product()/create_from_name(),
    # which derives one via ProductNormalizationService.build_canonical_key()
    # (CONNECT-005's hash-fallback guarantees a non-empty value for any
    # non-empty title) before ever constructing this schema.
    canonical_key: str = Field(min_length=1)
    description: str | None = None
    metadata: dict = Field(default_factory=dict)

    @field_validator("canonical_key")
    @classmethod
    def _canonical_key_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("canonical_key must not be blank")
        return stripped
