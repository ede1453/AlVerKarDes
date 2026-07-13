from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

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
def clear_state():
    global _service
    _service = UserValueIntelligenceService()
    return {"cleared": True}


@router.post("/savings/calculate")
def savings_calculate(payload: PayloadRequest):
    return _service.calculate_savings(
        **payload.payload
    )


@router.post("/savings/events")
def savings_event(payload: PayloadRequest):
    return _service.record_savings_event(
        **payload.payload
    )


@router.get("/savings/{user_id}")
def savings_summary(user_id: str):
    return _service.summarize_lifetime_savings(
        user_id=user_id
    )


@router.post("/price-trend")
def price_trend(payload: PayloadRequest):
    return _service.analyze_price_trend(
        **payload.payload
    )


@router.post("/purchase-timing")
def purchase_timing(payload: PayloadRequest):
    return _service.evaluate_purchase_timing(
        **payload.payload
    )


@router.post("/target-price")
def target_price(payload: PayloadRequest):
    return _service.calculate_target_price(
        **payload.payload
    )


@router.post("/alternatives")
def alternatives(payload: PayloadRequest):
    return _service.rank_alternatives(
        **payload.payload
    )


@router.post("/price-alert")
def price_alert(payload: PayloadRequest):
    return _service.evaluate_price_alert(
        **payload.payload
    )


@router.post("/watch")
def create_watch(payload: PayloadRequest):
    return _service.create_watch_entry(
        **payload.payload
    )


@router.post("/watch/expire")
def expire_watch(payload: PayloadRequest):
    return _service.expire_watch_entries(
        **payload.payload
    )


@router.post("/decision/explain")
def decision_explain(payload: PayloadRequest):
    return _service.explain_decision(
        **payload.payload
    )


@router.post("/decision/consistency")
def decision_consistency(
    payload: PayloadRequest,
):
    return _service.check_decision_consistency(
        **payload.payload
    )


@router.post("/journey/events")
def journey_event(payload: PayloadRequest):
    return _service.record_journey_event(
        **payload.payload
    )


@router.post("/journey/funnel")
def journey_funnel(payload: PayloadRequest):
    return _service.calculate_funnel(
        **payload.payload
    )


@router.post("/recommendation-value")
def recommendation_value(
    payload: PayloadRequest,
):
    return _service.calculate_recommendation_value(
        **payload.payload
    )


@router.post("/churn-risk")
def churn_risk(payload: PayloadRequest):
    return _service.calculate_churn_risk(
        **payload.payload
    )


@router.post("/retention-action")
def retention_action(payload: PayloadRequest):
    return _service.recommend_retention_action(
        **payload.payload
    )


@router.post("/purchases")
def purchases(payload: PayloadRequest):
    return _service.record_purchase(
        **payload.payload
    )


@router.post("/repeat-purchase")
def repeat_purchase(payload: PayloadRequest):
    return _service.check_repeat_purchase(
        **payload.payload
    )


@router.post("/dashboard")
def dashboard(payload: PayloadRequest):
    return _service.build_user_value_dashboard(
        **payload.payload
    )
