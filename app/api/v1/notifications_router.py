from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.notifications.notification_service import NotificationService


class NotificationDeliverRequest(BaseModel):
    user_id: str
    channels: list[str] = Field(default_factory=lambda: ["in_app"])
    title: str
    message: str
    payload: dict = Field(default_factory=dict)
    provider: str = "mock"


class NotificationFromSmartAlertRequest(BaseModel):
    user_id: str
    smart_alert: dict
    channels: list[str] = Field(default_factory=list)
    provider: str = "mock"


router = APIRouter(prefix="/notifications", tags=["notifications"])

_service = NotificationService()


@router.post("/deliver")
async def deliver_notification(payload: NotificationDeliverRequest):
    return _service.deliver(payload.model_dump())


@router.post("/from-smart-alert")
async def deliver_notification_from_smart_alert(payload: NotificationFromSmartAlertRequest):
    return _service.deliver_from_smart_alert(payload.model_dump())
