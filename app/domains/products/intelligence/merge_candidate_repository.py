from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.products.intelligence.merge_candidate_models import MergeCandidateModel


class MergeCandidateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_from_candidate(self, candidate):
        model = MergeCandidateModel(
            signature=candidate.signature,
            master_title=candidate.master_title,
            offer_count=candidate.offer_count,
            average_confidence=candidate.average_confidence,
            decision=candidate.decision,
            status="PENDING",
            offer_titles_json=candidate.offer_titles,
            sources_json=candidate.sources,
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return model

    async def list_pending(self, decision: str | None = None, limit: int = 50):
        stmt = select(MergeCandidateModel).where(
            MergeCandidateModel.status == "PENDING",
            MergeCandidateModel.deleted_at.is_(None),
        )

        if decision:
            stmt = stmt.where(MergeCandidateModel.decision == decision)

        stmt = stmt.order_by(MergeCandidateModel.created_at.asc()).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
   
    async def get_by_id(self, candidate_id: UUID):
        return await self.db.get(MergeCandidateModel, candidate_id)

    async def update_status(self, candidate_id: UUID, status: str):
        candidate = await self.get_by_id(candidate_id)
        if not candidate:
            return None

        candidate.status = status

        if status in {"APPROVED", "REJECTED", "NEEDS_REVIEW"}:
            candidate.reviewed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(candidate)
        return candidate
        
    async def mark_applied(self, candidate_id: UUID):
        candidate = await self.get_by_id(candidate_id)
        if not candidate:
            return None

        candidate.status = "APPLIED"
        candidate.applied_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(candidate)
        return candidate

    async def count_by_status(self, status: str):
        result = await self.db.execute(
            select(func.count())
            .select_from(MergeCandidateModel)
            .where(
                MergeCandidateModel.status == status,
                MergeCandidateModel.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one())



