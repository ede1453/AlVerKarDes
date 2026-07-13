from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.recommendations.models import Recommendation, RecommendationSession


class RecommendationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _json_safe(self, value):
        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, UUID):
            return str(value)

        if isinstance(value, dict):
            return {k: self._json_safe(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._json_safe(v) for v in value]

        return value

    async def create_session(self, *, query_text=None, input_url=None, metadata=None):
        session = RecommendationSession(
            query_text=query_text,
            input_url=input_url,
            metadata_json=metadata or {},
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def save_recommendation(
        self,
        *,
        session_id: UUID,
        decision: str,
        confidence: float,
        summary: str,
        payload: dict,
    ):
        recommendation = Recommendation(
            session_id=session_id,
            decision=str(decision),
            confidence=confidence,
            summary=summary,
            recommendation_payload=self._json_safe(payload),
        )
        self.db.add(recommendation)
        await self.db.commit()
        await self.db.refresh(recommendation)
        return recommendation

    async def list_for_session(self, session_id: UUID):
        result = await self.db.execute(
            select(Recommendation).where(
                Recommendation.session_id == session_id,
                Recommendation.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
