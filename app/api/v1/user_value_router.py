from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.domains.identity.dependencies import ensure_owner, get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.user_value.service import (
    UserValueIntelligenceService,
)

router = APIRouter(
    prefix="/user-value",
    tags=["user-value"],
)

_service = UserValueIntelligenceService()


class PayloadRequest(BaseModel):
    payload: dict[str, Any] = Field(
        default_factory=dict
    )


@router.post("/clear")
def clear_state(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    global _service
    _service = UserValueIntelligenceService()
    return {"cleared": True}


@router.post("/savings/calculate")
def savings_calculate(
    payload: PayloadRequest,
    # AUTH-006 Parça 2: OWNER_ONLY'den AUTHENTICATED'e KALICI olarak yeniden sınıflandırıldı — durumsuz hesaplayıcı, user_id yok (bkz. ADR-005).
    current_user=Depends(get_current_user),
):
    return _service.calculate_savings(
        **payload.payload
    )


@router.post("/savings/events")
def savings_event(
    payload: PayloadRequest,
    current_user=Depends(get_current_user),
):
    user_id = payload.payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id_required")
    ensure_owner(current_user, user_id)
    return _service.record_savings_event(
        **payload.payload
    )


@router.get("/savings/{user_id}")
def savings_summary(
    user_id: str,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return _service.summarize_lifetime_savings(
        user_id=user_id
    )


@router.post("/price-trend")
def price_trend(
    payload: PayloadRequest,
    # AUTH-006 Parça 2: OWNER_ONLY'den AUTHENTICATED'e KALICI olarak yeniden sınıflandırıldı — durumsuz hesaplayıcı, user_id yok (bkz. ADR-005).
    current_user=Depends(get_current_user),
):
    return _service.analyze_price_trend(
        **payload.payload
    )


@router.post("/purchase-timing")
def purchase_timing(
    payload: PayloadRequest,
    # AUTH-006 Parça 2: OWNER_ONLY'den AUTHENTICATED'e KALICI olarak yeniden sınıflandırıldı — durumsuz hesaplayıcı, user_id yok (bkz. ADR-005).
    current_user=Depends(get_current_user),
):
    return _service.evaluate_purchase_timing(
        **payload.payload
    )


@router.post("/target-price")
def target_price(
    payload: PayloadRequest,
    # AUTH-006 Parça 2: OWNER_ONLY'den AUTHENTICATED'e KALICI olarak yeniden sınıflandırıldı — durumsuz hesaplayıcı, user_id yok (bkz. ADR-005).
    current_user=Depends(get_current_user),
):
    return _service.calculate_target_price(
        **payload.payload
    )


@router.post("/alternatives")
def alternatives(
    payload: PayloadRequest,
    # AUTH-006 Parça 2: OWNER_ONLY'den AUTHENTICATED'e KALICI olarak yeniden sınıflandırıldı — durumsuz hesaplayıcı, user_id yok (bkz. ADR-005).
    current_user=Depends(get_current_user),
):
    return _service.rank_alternatives(
        **payload.payload
    )


@router.post("/price-alert")
def price_alert(
    payload: PayloadRequest,
    # AUTH-006 Parça 2: OWNER_ONLY'den AUTHENTICATED'e KALICI olarak yeniden sınıflandırıldı — durumsuz hesaplayıcı, user_id yok (bkz. ADR-005).
    current_user=Depends(get_current_user),
):
    return _service.evaluate_price_alert(
        **payload.payload
    )


@router.post("/watch")
def create_watch(
    payload: PayloadRequest,
    current_user=Depends(get_current_user),
):
    user_id = payload.payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id_required")
    ensure_owner(current_user, user_id)
    return _service.create_watch_entry(
        **payload.payload
    )


@router.post("/watch/expire")
def expire_watch(
    payload: PayloadRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.expire_watch_entries(
        **payload.payload
    )


@router.post("/decision/explain")
def decision_explain(
    payload: PayloadRequest,
    # AUTH-006 Parça 2: OWNER_ONLY'den AUTHENTICATED'e KALICI olarak yeniden sınıflandırıldı — durumsuz hesaplayıcı, user_id yok (bkz. ADR-005).
    current_user=Depends(get_current_user),
):
    return _service.explain_decision(
        **payload.payload
    )


@router.post("/decision/consistency")
def decision_consistency(
    payload: PayloadRequest,
    # AUTH-006 Parça 2: OWNER_ONLY'den AUTHENTICATED'e KALICI olarak yeniden sınıflandırıldı — durumsuz hesaplayıcı, user_id yok (bkz. ADR-005).
    current_user=Depends(get_current_user),
):
    return _service.check_decision_consistency(
        **payload.payload
    )


@router.post("/journey/events")
def journey_event(
    payload: PayloadRequest,
    current_user=Depends(get_current_user),
):
    user_id = payload.payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id_required")
    ensure_owner(current_user, user_id)
    return _service.record_journey_event(
        **payload.payload
    )


@router.post("/journey/funnel")
def journey_funnel(
    payload: PayloadRequest,
    current_user=Depends(get_current_user),
):
    user_id = payload.payload.get("user_id")
    if user_id is None:
        payload.payload["user_id"] = str(current_user.id)
    else:
        ensure_owner(current_user, user_id)
    return _service.calculate_funnel(
        **payload.payload
    )


@router.post("/recommendation-value")
def recommendation_value(
    payload: PayloadRequest,
    # AUTH-006 Parça 2: OWNER_ONLY'den AUTHENTICATED'e KALICI olarak yeniden sınıflandırıldı — durumsuz hesaplayıcı, user_id yok (bkz. ADR-005).
    current_user=Depends(get_current_user),
):
    return _service.calculate_recommendation_value(
        **payload.payload
    )


@router.post("/churn-risk")
def churn_risk(
    payload: PayloadRequest,
    # AUTH-006 Parça 2: OWNER_ONLY'den AUTHENTICATED'e KALICI olarak yeniden sınıflandırıldı — durumsuz hesaplayıcı, user_id yok (bkz. ADR-005).
    current_user=Depends(get_current_user),
):
    return _service.calculate_churn_risk(
        **payload.payload
    )


@router.post("/retention-action")
def retention_action(
    payload: PayloadRequest,
    # AUTH-006 Parça 2: OWNER_ONLY'den AUTHENTICATED'e KALICI olarak yeniden sınıflandırıldı — durumsuz hesaplayıcı, user_id yok (bkz. ADR-005).
    current_user=Depends(get_current_user),
):
    return _service.recommend_retention_action(
        **payload.payload
    )


@router.post("/purchases")
def purchases(
    payload: PayloadRequest,
    current_user=Depends(get_current_user),
):
    user_id = payload.payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id_required")
    ensure_owner(current_user, user_id)
    return _service.record_purchase(
        **payload.payload
    )


@router.post("/repeat-purchase")
def repeat_purchase(
    payload: PayloadRequest,
    current_user=Depends(get_current_user),
):
    user_id = payload.payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id_required")
    ensure_owner(current_user, user_id)
    return _service.check_repeat_purchase(
        **payload.payload
    )


@router.post("/dashboard")
def dashboard(
    payload: PayloadRequest,
    current_user=Depends(get_current_user),
):
    user_id = payload.payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id_required")
    ensure_owner(current_user, user_id)
    return _service.build_user_value_dashboard(
        **payload.payload
    )
