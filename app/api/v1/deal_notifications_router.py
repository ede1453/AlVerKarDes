from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.deal_notifications.service import (
    DealNotificationService,
)

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
def clear_deal_notifications():
    return _service.clear()


@router.post("/preferences")
def set_preferences(
    payload: PreferenceRequest,
):
    return _service.preferences.set_preferences(
        **payload.model_dump()
    )


@router.get("/preferences/{user_id}")
def get_preferences(user_id: str):
    return _service.preferences.get_preferences(
        user_id
    )


@router.post("/build")
def build_notification(
    payload: NotificationRequest,
):
    return _service.build_notification(
        **payload.model_dump()
    )


@router.post(
    "/{notification_id}/delivered"
)
def mark_delivered(
    notification_id: str,
    payload: DeliveryRequest,
):
    return _service.mark_delivered(
        notification_id=notification_id,
        channel=payload.channel,
    )


@router.get("")
def list_notifications(
    user_id: str | None = None,
    status: str | None = None,
):
    return _service.list_notifications(
        user_id=user_id,
        status=status,
    )
