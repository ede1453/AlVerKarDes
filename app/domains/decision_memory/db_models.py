import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DecisionMemoryModel(Base):
    __tablename__ = "decision_memory"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    product_id: Mapped[str | None] = mapped_column(String, nullable=True)
    offer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String, nullable=False, default="DE")
    final_decision: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str | None] = mapped_column(String, nullable=True)
    opportunity_level: Mapped[str | None] = mapped_column(String, nullable=True)
    deal_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    authenticity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String, nullable=True)
    reason_codes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    decision_context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    outcome: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
