from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.decision_memory.db_models import DecisionMemoryModel
from app.domains.decision_memory.decision_memory_models import DecisionMemoryRecord


class InMemoryDecisionMemoryRepository:
    """Plain in-memory test double. Not used by the API anymore (see
    DecisionMemoryRepository below) -- kept for unit tests that want a
    repository without a real database."""

    def __init__(self):
        self.records = {}

    async def save(self, record):
        self.records[record.id] = record
        return record

    async def get(self, decision_id: str):
        return self.records.get(decision_id)

    async def update_outcome(self, decision_id: str, outcome: dict):
        record = self.records.get(decision_id)
        if record is None:
            return None

        record.outcome = outcome
        return record


def _to_record(row: DecisionMemoryModel) -> DecisionMemoryRecord:
    return DecisionMemoryRecord(
        id=str(row.id),
        user_id=str(row.user_id) if row.user_id is not None else None,
        product_id=row.product_id,
        offer_id=row.offer_id,
        country=row.country,
        final_decision=row.final_decision,
        confidence=row.confidence,
        risk_level=row.risk_level,
        opportunity_level=row.opportunity_level,
        deal_score=row.deal_score,
        authenticity_score=row.authenticity_score,
        recommendation=row.recommendation,
        reason_codes=list(row.reason_codes or []),
        decision_context=dict(row.decision_context or {}),
        generated_at=row.generated_at,
        outcome=row.outcome,
    )


class DecisionMemoryRepository:
    """Postgres-backed repository (AUTH-006 Part 2, ADR-005).

    Before this, the class of this same name silently extended
    InMemoryDecisionMemoryRepository and never touched the database at all,
    even though migration 0005 had already created a real `decision_memory`
    table -- the table was pure dead schema. This version actually reads
    from and writes to it. There is no in-memory fallback; a real
    AsyncSession is required.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, record: DecisionMemoryRecord) -> DecisionMemoryRecord:
        row = DecisionMemoryModel(
            id=UUID(record.id),
            user_id=UUID(record.user_id) if record.user_id else None,
            product_id=record.product_id,
            offer_id=record.offer_id,
            country=record.country,
            final_decision=record.final_decision,
            confidence=record.confidence,
            risk_level=record.risk_level,
            opportunity_level=record.opportunity_level,
            deal_score=record.deal_score,
            authenticity_score=record.authenticity_score,
            recommendation=record.recommendation,
            reason_codes=list(record.reason_codes),
            decision_context=dict(record.decision_context),
            outcome=record.outcome,
            generated_at=record.generated_at,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return _to_record(row)

    async def get(self, decision_id: str) -> DecisionMemoryRecord | None:
        try:
            key = UUID(decision_id)
        except ValueError:
            return None

        row = await self.db.get(DecisionMemoryModel, key)
        if row is None:
            return None
        return _to_record(row)

    async def update_outcome(self, decision_id: str, outcome: dict) -> DecisionMemoryRecord | None:
        try:
            key = UUID(decision_id)
        except ValueError:
            return None

        row = await self.db.get(DecisionMemoryModel, key)
        if row is None:
            return None

        row.outcome = outcome
        await self.db.commit()
        await self.db.refresh(row)
        return _to_record(row)

    async def list_recent_by_user(self, user_id: str, limit: int = 5) -> list[DecisionMemoryRecord]:
        """VISION-000: the read side of "AI Shopping Memory" -- a plain
        recency query, no semantic search/embeddings (see ADR-018, that's
        deliberately out of scope for this slice). Uses the `user_id` index
        (migration 0017_decision_memory_owner) added when AUTH-006 Part 1
        gave decision_memory an owner column, so this is not a new index
        need -- just its first real consumer."""
        try:
            key = UUID(user_id)
        except ValueError:
            return []

        result = await self.db.execute(
            select(DecisionMemoryModel)
            .where(DecisionMemoryModel.user_id == key)
            .order_by(DecisionMemoryModel.generated_at.desc())
            .limit(limit)
        )
        return [_to_record(row) for row in result.scalars().all()]
