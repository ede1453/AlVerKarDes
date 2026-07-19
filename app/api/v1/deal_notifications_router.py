from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.domains.deal_notifications.service import (
    DealNotificationService,
)
from app.domains.identity.dependencies import ensure_owner, get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter(
    prefix="/deal-notifications",
    tags=["deal-notifications"],
)

_service = DealNotificationService()


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
def set_preferences(
    payload: PreferenceRequest,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)
    return _service.preferences.set_preferences(
        **payload.model_dump()
    )


@router.get("/preferences/{user_id}")
def get_preferences(
    user_id: str,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return _service.preferences.get_preferences(
        user_id
    )


@router.post("/build")
def build_notification(
    payload: NotificationRequest,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)
    return _service.build_notification(
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
