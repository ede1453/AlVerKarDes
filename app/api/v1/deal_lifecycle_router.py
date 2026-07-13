from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.deal_lifecycle.service import (
    DealLifecycleService,
)

router = APIRouter(
    prefix="/deal-lifecycle",
    tags=["deal-lifecycle"],
)

_service = DealLifecycleService()


class DealRegistrationRequest(BaseModel):
    source_id: str
    external_offer_id: str
    canonical_product_key: str
    observed_at: str
    price: float
    currency: str
    payload: dict[str, Any] = Field(
        default_factory=dict
    )


class DecisionVersionRequest(BaseModel):
    decision: str
    confidence: float
    explanation: str
    evidence: dict[str, Any] = Field(
        default_factory=dict
    )


class WatchPolicyRequest(BaseModel):
    user_id: str
    product_key: str
    target_price: float | None = None
    minimum_discount_pct: float = 0
    minimum_confidence: float = 60
    allowed_sources: list[str] = Field(
        default_factory=list
    )


class WatchEvaluationRequest(BaseModel):
    user_id: str
    opportunity: dict[str, Any] = Field(
        default_factory=dict
    )


class StatusTransitionRequest(BaseModel):
    new_status: str
    reason: str
    actor: str = "system"


@router.post("/clear")
def clear_deal_lifecycle():
    global _service
    _service = DealLifecycleService()
    return {"cleared": True}


@router.post("/deals")
def register_deal(
    payload: DealRegistrationRequest,
):
    return _service.register_deal(
        **payload.model_dump()
    )


@router.get("/deals")
def list_deals(
    status: str | None = None,
    product_key: str | None = None,
    source_id: str | None = None,
):
    return _service.list_deals(
        status=status,
        product_key=product_key,
        source_id=source_id,
    )


@router.get("/deals/{deal_id}")
def get_deal(deal_id: str):
    deal = _service.get_deal(deal_id)

    if deal is None:
        raise HTTPException(
            status_code=404,
            detail="DEAL_NOT_FOUND",
        )

    return deal


@router.post(
    "/deals/{deal_id}/decision-versions"
)
def append_decision_version(
    deal_id: str,
    payload: DecisionVersionRequest,
):
    return _service.append_decision_version(
        deal_id=deal_id,
        **payload.model_dump(),
    )


@router.get(
    "/deals/{deal_id}/decision-versions"
)
def get_decision_versions(
    deal_id: str,
):
    return _service.get_decision_versions(
        deal_id
    )


@router.post(
    "/deals/{deal_id}/transition"
)
def transition_deal_status(
    deal_id: str,
    payload: StatusTransitionRequest,
):
    return _service.transition_status(
        deal_id=deal_id,
        **payload.model_dump(),
    )


@router.post("/watch-policies")
def create_watch_policy(
    payload: WatchPolicyRequest,
):
    return _service.create_watch_policy(
        **payload.model_dump()
    )


@router.post("/watch-policies/evaluate")
def evaluate_watch_policies(
    payload: WatchEvaluationRequest,
):
    return _service.evaluate_watch_policies(
        user_id=payload.user_id,
        opportunity=payload.opportunity,
    )


@router.get("/events")
def list_events(
    deal_id: str | None = None,
    event_type: str | None = None,
):
    return _service.list_events(
        deal_id=deal_id,
        event_type=event_type,
    )
