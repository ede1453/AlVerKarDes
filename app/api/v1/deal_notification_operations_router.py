from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.deal_notifications.operations import (
    DealNotificationOperationsService,
)

router = APIRouter(
    prefix="/deal-notification-operations",
    tags=["deal-notification-operations"],
)

_service = DealNotificationOperationsService()


class DeliveryAttemptRequest(BaseModel):
    notification_id: str
    channel: str
    provider: str
    successful: bool
    error: str | None = None
    latency_ms: float = 0


class IdempotencyRequest(BaseModel):
    user_id: str
    deal_id: str
    channel: str
    window_key: str


class EscalationRequest(BaseModel):
    notification_id: str
    current_channel: str
    fallback_channels: list[str] = Field(
        default_factory=list
    )
    trigger_after_failures: int = 2


class EscalationCompleteRequest(BaseModel):
    delivered_channel: str


class DigestRequest(BaseModel):
    user_id: str
    notifications: list[dict[str, Any]] = Field(
        default_factory=list
    )
    period_start: str
    period_end: str
    maximum_items: int = 20


class EngagementRequest(BaseModel):
    notification_id: str
    user_id: str
    event_type: str
    channel: str
    occurred_at: str | None = None
    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


@router.post("/clear")
def clear_operations():
    return _service.clear()


@router.post("/delivery-attempts")
def record_attempt(
    payload: DeliveryAttemptRequest,
):
    return _service.record_delivery_attempt(
        **payload.model_dump()
    )


@router.get(
    "/delivery-attempts/{notification_id}"
)
def get_attempts(notification_id: str):
    return _service.get_delivery_attempts(
        notification_id=notification_id
    )


@router.post("/idempotency/reserve")
def reserve_idempotency(
    payload: IdempotencyRequest,
):
    return _service.reserve_idempotency_key(
        **payload.model_dump()
    )


@router.post("/escalations")
def create_escalation(
    payload: EscalationRequest,
):
    return _service.create_escalation(
        **payload.model_dump()
    )


@router.post(
    "/escalations/{escalation_id}/complete"
)
def complete_escalation(
    escalation_id: str,
    payload: EscalationCompleteRequest,
):
    return _service.complete_escalation(
        escalation_id=escalation_id,
        delivered_channel=(
            payload.delivered_channel
        ),
    )


@router.post("/digests")
def build_digest(
    payload: DigestRequest,
):
    return _service.build_digest(
        **payload.model_dump()
    )


@router.post("/engagement")
def record_engagement(
    payload: EngagementRequest,
):
    return _service.record_engagement(
        **payload.model_dump()
    )


@router.get("/engagement/metrics")
def get_engagement_metrics(
    user_id: str | None = None,
    channel: str | None = None,
):
    return _service.calculate_engagement_metrics(
        user_id=user_id,
        channel=channel,
    )
