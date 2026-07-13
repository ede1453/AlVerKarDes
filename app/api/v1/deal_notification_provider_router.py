from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.deal_notifications.provider_governance import (
    NotificationProviderGovernanceService,
)

router = APIRouter(
    prefix="/deal-notification-providers",
    tags=["deal-notification-providers"],
)

_service = NotificationProviderGovernanceService()


class ProviderRequest(BaseModel):
    provider_id: str
    channel: str
    priority: int = 100
    enabled: bool = True
    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class DeliveryPolicyRequest(BaseModel):
    notification: dict[str, Any] = Field(
        default_factory=dict
    )
    user_preferences: dict[str, Any] = Field(
        default_factory=dict
    )
    provider_available: bool
    unsubscribe_status: bool


class SubscriptionRequest(BaseModel):
    user_id: str
    channel: str
    subscribed: bool
    source: str


class ExperimentRequest(BaseModel):
    experiment_id: str
    variants: list[str] = Field(
        default_factory=list
    )
    enabled: bool = True


class PerformanceRequest(BaseModel):
    delivery_attempts: list[dict[str, Any]] = Field(
        default_factory=list
    )
    engagement_events: list[dict[str, Any]] = Field(
        default_factory=list
    )


@router.post("/clear")
def clear_provider_governance():
    global _service
    _service = NotificationProviderGovernanceService()
    return {"cleared": True}


@router.post("/providers")
def register_provider(
    payload: ProviderRequest,
):
    return _service.providers.register_provider(
        **payload.model_dump()
    )


@router.get("/providers/select")
def select_provider(channel: str):
    return _service.providers.select_provider(
        channel=channel
    )


@router.post("/delivery-policy/evaluate")
def evaluate_delivery_policy(
    payload: DeliveryPolicyRequest,
):
    return _service.delivery_policy.evaluate(
        **payload.model_dump()
    )


@router.post("/subscriptions")
def set_subscription(
    payload: SubscriptionRequest,
):
    return _service.compliance.set_subscription(
        **payload.model_dump()
    )


@router.get("/subscriptions/unsubscribed")
def is_unsubscribed(
    user_id: str,
    channel: str,
):
    return {
        "user_id": user_id,
        "channel": channel.lower(),
        "unsubscribed": (
            _service.compliance.is_unsubscribed(
                user_id=user_id,
                channel=channel,
            )
        ),
    }


@router.post("/experiments")
def create_experiment(
    payload: ExperimentRequest,
):
    return _service.experiments.create_experiment(
        **payload.model_dump()
    )


@router.get(
    "/experiments/{experiment_id}/assign"
)
def assign_variant(
    experiment_id: str,
    user_id: str,
):
    return _service.experiments.assign_variant(
        experiment_id=experiment_id,
        user_id=user_id,
    )


@router.post("/performance")
def summarize_performance(
    payload: PerformanceRequest,
):
    return _service.performance.summarize(
        **payload.model_dump()
    )
