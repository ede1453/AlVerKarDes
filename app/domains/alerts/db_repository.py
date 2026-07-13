from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.alerts.db_models import AlertRuleModel
from app.domains.alerts.schemas import AlertRuleCreate


class AlertRuleDBRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: AlertRuleCreate):
        rule = AlertRuleModel(**payload.model_dump())
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def list_active_for_offer(self, offer_id: UUID):
        result = await self.db.execute(
            select(AlertRuleModel).where(
                AlertRuleModel.offer_id == offer_id,
                AlertRuleModel.is_active.is_(True),
                AlertRuleModel.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def soft_delete(self, rule_id: UUID):
        rule = await self.db.get(AlertRuleModel, rule_id)
        if not rule:
            return None
        rule.is_active = False
        await self.db.commit()
        await self.db.refresh(rule)
        return rule
