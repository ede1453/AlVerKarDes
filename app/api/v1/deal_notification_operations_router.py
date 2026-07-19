from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.deal_notifications.operations import (
    DealNotificationOperationsService,
)
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole

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
def clear_operations(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.clear()


@router.post("/delivery-attempts")
def record_attempt(
    payload: DeliveryAttemptRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.record_delivery_attempt(
        **payload.model_dump()
    )


@router.get(
    "/delivery-attempts/{notification_id}"
)
def get_attempts(
    notification_id: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.get_delivery_attempts(
        notification_id=notification_id
    )


@router.post("/idempotency/reserve")
def reserve_idempotency(
    payload: IdempotencyRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.reserve_idempotency_key(
        **payload.model_dump()
    )


@router.post("/escalations")
def create_escalation(
    payload: EscalationRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
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
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
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
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.build_digest(
        **payload.model_dump()
    )


@router.post("/engagement")
def record_engagement(
    payload: EngagementRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.record_engagement(
        **payload.model_dump()
    )


@router.get("/engagement/metrics")
def get_engagement_metrics(
    user_id: str | None = None,
    channel: str | None = None,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.calculate_engagement_metrics(
        user_id=user_id,
        channel=channel,
    )
