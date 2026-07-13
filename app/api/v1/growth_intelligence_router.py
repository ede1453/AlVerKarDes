from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.growth_intelligence.service import (
    GrowthRevenueIntelligenceService,
)

router = APIRouter(
    prefix="/growth-intelligence",
    tags=["growth-intelligence"],
)

_service = GrowthRevenueIntelligenceService()


class PayloadRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/clear")
def clear_state():
    global _service
    _service = GrowthRevenueIntelligenceService()
    return {"cleared": True}


_METHODS = {
    "cac": "calculate_customer_acquisition_cost",
    "ltv": "calculate_lifetime_value",
    "ltv-cac": "calculate_ltv_cac_ratio",
    "mau": "calculate_monthly_active_users",
    "dau": "calculate_daily_active_users",
    "stickiness": "calculate_stickiness",
    "activation": "calculate_activation_rate",
    "retention": "calculate_retention_rate",
    "churn": "calculate_churn_rate",
    "growth-funnel": "build_growth_funnel",
    "affiliate-click": "record_affiliate_click",
    "affiliate-conversion": "record_affiliate_conversion",
    "affiliate-conversion-rate": "calculate_affiliate_conversion_rate",
    "revenue-per-click": "calculate_revenue_per_click",
    "revenue-per-user": "calculate_revenue_per_user",
    "revenue-independence": "evaluate_revenue_independence",
    "campaign-create": "create_campaign",
    "campaign-spend": "record_campaign_spend",
    "campaign-roi": "calculate_campaign_roi",
    "campaign-budget": "evaluate_campaign_budget",
    "segment-create": "create_user_segment",
    "segment-membership": "evaluate_segment_membership",
    "behavioral-segment": "build_behavioral_segment",
    "cohort-create": "create_cohort",
    "cohort-retention": "calculate_cohort_retention",
    "reactivation": "calculate_reactivation_rate",
    "retailer-snapshot": "record_retailer_snapshot",
    "retailer-quality": "calculate_retailer_quality",
    "retailer-conversion": "calculate_retailer_conversion",
    "retailer-scorecard": "build_retailer_scorecard",
    "experiment-create": "create_growth_experiment",
    "experiment-result": "record_experiment_result",
    "experiment-evaluate": "evaluate_experiment",
    "growth-event": "record_growth_event",
    "north-star": "calculate_north_star_metric",
    "gmv": "calculate_gross_merchandise_value",
    "take-rate": "calculate_take_rate",
    "revenue-quality": "calculate_revenue_quality",
    "growth-health": "build_growth_health_report",
    "executive-dashboard": "build_executive_dashboard",
}


@router.post("/{operation}")
def execute_operation(
    operation: str,
    payload: PayloadRequest,
):
    method_name = _METHODS.get(operation)

    if method_name is None:
        return {
            "executed": False,
            "reason": "UNKNOWN_OPERATION",
        }

    method = getattr(_service, method_name)
    return method(**payload.payload)
