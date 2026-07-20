from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Brand(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    website: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(2))
    trust_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "categories"

    parent_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "products"

    brand_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("brands.id"))
    category_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str | None] = mapped_column(String(300))
    model_number: Mapped[str | None] = mapped_column(String(200))
    gtin: Mapped[str | None] = mapped_column(String(32))
    manufacturer_sku: Mapped[str | None] = mapped_column(String(200))
    # NOT NULL (migration 0021) -- every product must be born with a real
    # canonical_key, guaranteed at the API boundary by ProductCreate's
    # required field (see schemas.py).
    canonical_key: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class ProductVariant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "product_variants"

    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_name: Mapped[str] = mapped_column(String(240), nullable=False)
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict)
    gtin: Mapped[str | None] = mapped_column(String(32))
    manufacturer_sku: Mapped[str | None] = mapped_column(String(200))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class Specification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "specifications"

    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id"))
    spec_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    source: Mapped[str | None] = mapped_column(String(200))
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))
