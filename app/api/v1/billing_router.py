from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.domains.billing.db_models import SubscriptionTier
from app.domains.billing.factory import get_payment_provider
from app.domains.billing.provider import PaymentProvider
from app.domains.billing.repository import SubscriptionDBRepository
from app.domains.billing.service import SubscriptionService
from app.domains.identity.dependencies import ensure_owner, get_current_user

router = APIRouter(prefix="/billing", tags=["billing"])


def _service(db: AsyncSession, payment_provider: PaymentProvider | None = None) -> SubscriptionService:
    return SubscriptionService(repository=SubscriptionDBRepository(db), payment_provider=payment_provider)


class CheckoutRequest(BaseModel):
    user_id: str
    plan: str


class CancelRequest(BaseModel):
    user_id: str


@router.get("/plans")
def list_plans():
    # PUBLIC -- static plan comparison data, no auth needed. Only the
    # limits actually enforced elsewhere (watchlist_router.py,
    # deal_notifications_router.py) are reflected here; no aspirational
    # feature ("priority delivery" etc.) is claimed that isn't real yet --
    # see ADR-016 Sonuc Raporu.
    return {
        "plans": [
            {
                "tier": SubscriptionTier.FREE.value,
                "watchlist_limit": settings.FREE_TIER_WATCHLIST_LIMIT,
                "threshold_customization": False,
            },
            {
                "tier": SubscriptionTier.PREMIUM.value,
                "watchlist_limit": None,
                "threshold_customization": True,
            },
        ]
    }


@router.get("/subscription/{user_id}")
async def get_subscription(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return await _service(db).get_current(user_id)


@router.post("/checkout")
async def checkout(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    payment_provider: PaymentProvider = Depends(get_payment_provider),
):
    ensure_owner(current_user, payload.user_id)
    if payload.plan not in (SubscriptionTier.FREE.value, SubscriptionTier.PREMIUM.value):
        raise HTTPException(status_code=422, detail={"code": "INVALID_PLAN"})
    return await _service(db, payment_provider).checkout(user_id=payload.user_id, plan=payload.plan)


@router.post("/cancel")
async def cancel(
    payload: CancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    payment_provider: PaymentProvider = Depends(get_payment_provider),
):
    ensure_owner(current_user, payload.user_id)
    return await _service(db, payment_provider).cancel(user_id=payload.user_id)
