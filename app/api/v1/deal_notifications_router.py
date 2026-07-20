from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.billing.db_models import SubscriptionTier
from app.domains.billing.repository import SubscriptionDBRepository
from app.domains.billing.service import SubscriptionService
from app.domains.deal_notifications.repository import NotificationPreferenceDBRepository
from app.domains.deal_notifications.service import (
    DealNotificationService,
    NotificationPreferenceService,
)
from app.domains.identity.dependencies import ensure_owner, get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter(
    prefix="/deal-notifications",
    tags=["deal-notifications"],
)

# CLIENT-002g: this singleton keeps _notifications (in-memory notification
# history/delivery-tracking, unchanged, out of this round's scope) alive
# across requests. Its own .preferences attribute (in-memory default) is
# NOT used for real preference reads anymore -- see _preferences_service()
# below, constructed fresh per request with a real DB session, same
# decision_memory_router.py/watchlist_router.py pattern (CLIENT-002e).
_service = DealNotificationService()


def _preferences_service(db: AsyncSession) -> NotificationPreferenceService:
    return NotificationPreferenceService(repository=NotificationPreferenceDBRepository(db))


class PreferenceRequest(BaseModel):
    user_id: str
    enabled_channels: list[str] = Field(
        default_factory=lambda: ["in_app"]
    )
    minimum_confidence: float = 70
    minimum_discount_pct: float = 10
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"


class NotificationRequest(BaseModel):
    user_id: str
    deal: dict[str, Any] = Field(
        default_factory=dict
    )
    at_time: str


class DeliveryRequest(BaseModel):
    channel: str


@router.post("/clear")
def clear_deal_notifications(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.clear()


@router.post("/preferences")
async def set_preferences(
    payload: PreferenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)

    # BILL-001: threshold customization (minimum_confidence/minimum_discount_pct)
    # is PREMIUM-only. CLIENT-002g built this as a full-replace endpoint
    # (the whole preference set is sent every time, not a partial patch) --
    # so a FREE user is allowed to change channels/quiet-hours freely, but
    # only rejected if the THRESHOLD fields specifically differ from what's
    # already stored. Existing values are never silently reset: the current
    # row is preserved untouched on rejection, see ADR-016 Sonuc Raporu
    # ("geriye donuk kisitlama, veri korunarak").
    subscription = await SubscriptionService(repository=SubscriptionDBRepository(db)).get_current(payload.user_id)
    if subscription["tier"] == SubscriptionTier.FREE.value:
        current = await _preferences_service(db).get_preferences(payload.user_id)
        if (
            payload.minimum_confidence != current["minimum_confidence"]
            or payload.minimum_discount_pct != current["minimum_discount_pct"]
        ):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "THRESHOLD_CUSTOMIZATION_REQUIRES_PREMIUM",
                    "message": "Alert threshold customization requires a PREMIUM subscription.",
                },
            )

    return await _preferences_service(db).set_preferences(
        **payload.model_dump()
    )


@router.get("/preferences/{user_id}")
async def get_preferences(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return await _preferences_service(db).get_preferences(
        user_id
    )


@router.post("/build")
async def build_notification(
    payload: NotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)
    preferences = await _preferences_service(db).get_preferences(payload.user_id)
    return await _service.build_notification(
        preferences=preferences,
        **payload.model_dump()
    )


@router.post(
    "/{notification_id}/delivered"
)
def mark_delivered(
    notification_id: str,
    payload: DeliveryRequest,
    current_user=Depends(get_current_user),
):
    notification = _service.get_notification(notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="notification_not_found")
    ensure_owner(current_user, notification["user_id"])
    return _service.mark_delivered(
        notification_id=notification_id,
        channel=payload.channel,
    )


@router.get("")
def list_notifications(
    user_id: str | None = None,
    status: str | None = None,
    current_user=Depends(get_current_user),
):
    if user_id is None:
        user_id = str(current_user.id)
    else:
        ensure_owner(current_user, user_id)
    return _service.list_notifications(
        user_id=user_id,
        status=status,
    )
