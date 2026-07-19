from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.alerts.db_repository import AlertRuleDBRepository
from app.domains.alerts.schemas import AlertRuleCreate, AlertRuleRead
from app.domains.identity.dependencies import ensure_owner, get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/rules", response_model=AlertRuleRead, status_code=201)
async def create_alert_rule(
    payload: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)
    rule = await AlertRuleDBRepository(db).create(payload)
    return rule


@router.get("/rules/offer/{offer_id}", response_model=list[AlertRuleRead])
async def list_alert_rules_for_offer(
    offer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rules = await AlertRuleDBRepository(db).list_active_for_offer(offer_id)
    return [rule for rule in rules if rule.user_id == current_user.id]


@router.delete("/rules/{rule_id}", response_model=AlertRuleRead)
async def delete_alert_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    repository = AlertRuleDBRepository(db)
    rule = await repository.get(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="alert_rule_not_found")
    ensure_owner(current_user, rule.user_id)
    rule = await repository.soft_delete(rule_id)
    return rule
