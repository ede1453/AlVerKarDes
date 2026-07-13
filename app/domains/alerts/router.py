from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.alerts.db_repository import AlertRuleDBRepository
from app.domains.alerts.schemas import AlertRuleCreate, AlertRuleRead

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/rules", response_model=AlertRuleRead, status_code=201)
async def create_alert_rule(payload: AlertRuleCreate, db: AsyncSession = Depends(get_db)):
    rule = await AlertRuleDBRepository(db).create(payload)
    return rule


@router.get("/rules/offer/{offer_id}", response_model=list[AlertRuleRead])
async def list_alert_rules_for_offer(offer_id: UUID, db: AsyncSession = Depends(get_db)):
    return await AlertRuleDBRepository(db).list_active_for_offer(offer_id)


@router.delete("/rules/{rule_id}", response_model=AlertRuleRead)
async def delete_alert_rule(rule_id: UUID, db: AsyncSession = Depends(get_db)):
    rule = await AlertRuleDBRepository(db).soft_delete(rule_id)
    return rule
