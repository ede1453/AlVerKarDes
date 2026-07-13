from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Store(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "stores"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    website: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str] = mapped_column(String(2), default="DE", nullable=False)
    affiliate_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    affiliate_network: Mapped[str | None] = mapped_column(String(120))
    trust_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class Offer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "offers"

    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id"))
    store_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    store_sku: Mapped[str | None] = mapped_column(String(200))
    title_on_store: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class Price(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "prices"

    offer_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    original_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    shipping_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    stock_status: Mapped[str | None] = mapped_column(String(80))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
