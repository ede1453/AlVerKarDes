from pydantic import BaseModel, Field, HttpUrl


class ProductNormalizationInput(BaseModel):
    product_url: HttpUrl | None = None
    product_name: str | None = None
    raw_title: str | None = None
    country: str = "DE"
    language: str = "en"


class VariantAttributes(BaseModel):
    color: str | None = None
    storage: str | None = None
    memory: str | None = None
    size: str | None = None
    connectivity: str | None = None
    other: dict = Field(default_factory=dict)


class ProductIdentity(BaseModel):
    brand: str | None = None
    product_family: str | None = None
    model: str | None = None
    category_hint: str | None = None
    variant: VariantAttributes = Field(default_factory=VariantAttributes)
    canonical_key: str | None = None
    confidence: float = Field(ge=0, le=100, default=0)
    missing_fields: list[str] = Field(default_factory=list)
    raw_input: dict = Field(default_factory=dict)
