from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RecommendationSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "recommendation_sessions"

    user_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    query_text: Mapped[str | None] = mapped_column(Text)
    input_url: Mapped[str | None] = mapped_column(Text)
    product_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    status: Mapped[str] = mapped_column(String(80), default="CREATED", nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default="en")
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    country: Mapped[str] = mapped_column(String(2), default="DE")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class Recommendation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "recommendations"

    session_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recommendation_sessions.id"), nullable=False)
    product_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
