from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.internal_service_auth import require_internal_service_key
from app.domains.consumer_trust.service import (
    ConsumerTrustService,
)
from app.domains.identity.dependencies import ensure_owner, get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter(
    prefix="/consumer-trust",
    tags=["consumer-trust"],
)

_service = ConsumerTrustService()


class GenericPayload(BaseModel):
    payload: dict[str, Any] = Field(
        default_factory=dict
    )


class DeliveryRecordRequest(BaseModel):
    user_id: str
    channel: str
    delivered_at: str | None = None


@router.post("/clear")
def clear_state(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    global _service
    _service = ConsumerTrustService()
    return {"cleared": True}


@router.post("/fatigue")
def calculate_fatigue(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.calculate_notification_fatigue(
        **payload.payload
    )


@router.post("/deliveries")
def record_delivery(
    payload: DeliveryRecordRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.record_delivery(
        **payload.model_dump()
    )


@router.post("/frequency-cap")
def evaluate_frequency_cap(
    payload: GenericPayload,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.evaluate_frequency_cap(
        **payload.payload
    )


@router.post("/provider-health")
def provider_health(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.calculate_provider_health(
        **payload.payload
    )


@router.post("/provider-fallback")
def provider_fallback(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.select_provider_fallback(
        **payload.payload
    )


@router.post("/delivery-sla")
def delivery_sla(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.evaluate_delivery_sla(
        **payload.payload
    )


@router.post("/feedback")
def record_feedback(
    payload: GenericPayload,
    current_user=Depends(get_current_user),
):
    return _service.record_feedback(
        **payload.payload
    )


@router.post("/acceptance-metrics")
def acceptance_metrics(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.calculate_acceptance_metrics(
        **payload.payload
    )


@router.post("/false-positive")
def false_positive(
    payload: GenericPayload,
    current_user=Depends(get_current_user),
):
    return _service.report_false_positive(
        **payload.payload
    )


@router.post("/source-trust")
def source_trust(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.adjust_source_trust(
        **payload.payload
    )


@router.post("/feedback-summary")
def feedback_summary(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.summarize_feedback(
        **payload.payload
    )


@router.post("/budget-policy")
def budget_policy(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.evaluate_budget_policy(
        **payload.payload
    )


@router.post("/category-quota")
def category_quota(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.evaluate_category_quota(
        **payload.payload
    )


@router.post("/saved-searches")
def create_saved_search(
    payload: GenericPayload,
    current_user=Depends(get_current_user),
):
    user_id = payload.payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id_required")
    ensure_owner(current_user, user_id)
    return _service.create_saved_search(
        **payload.payload
    )


@router.get("/saved-searches/{user_id}")
def list_saved_searches(
    user_id: str,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return _service.list_saved_searches(
        user_id=user_id
    )


@router.post("/compare-deals")
def compare_deals(
    payload: GenericPayload,
):
    return _service.compare_deals(
        **payload.payload
    )


@router.post("/purchase-intents")
def purchase_intent(
    payload: GenericPayload,
    current_user=Depends(get_current_user),
):
    user_id = payload.payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id_required")
    ensure_owner(current_user, user_id)
    return _service.record_purchase_intent(
        **payload.payload
    )


@router.post("/conversions")
def conversions(
    payload: GenericPayload,
    current_user=Depends(get_current_user),
):
    user_id = payload.payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id_required")
    ensure_owner(current_user, user_id)
    return _service.attribute_conversion(
        **payload.payload
    )


@router.post("/affiliate-disclosure")
def affiliate_disclosure(
    payload: GenericPayload,
):
    return _service.build_affiliate_disclosure(
        **payload.payload
    )


@router.post("/sponsored-compliance")
def sponsored_compliance(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.validate_sponsored_separation(
        **payload.payload
    )


@router.post("/recommendation-audit")
def recommendation_audit(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.audit_recommendation(
        **payload.payload
    )


@router.post("/trust-dashboard")
def trust_dashboard(
    payload: GenericPayload,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.build_trust_dashboard(
        **payload.payload
    )
