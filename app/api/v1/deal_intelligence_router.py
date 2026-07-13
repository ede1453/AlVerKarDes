from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.deal_intelligence.service import (
    DealConfidenceEngine,
    DealIntelligenceService,
    DiscountTruthEngine,
    OpportunityRanker,
    PriceHistoryAnalyzer,
    RecommendationBridge,
)

router = APIRouter(
    prefix="/deal-intelligence",
    tags=["deal-intelligence"],
)


class PriceHistoryRequest(BaseModel):
    current_price: float
    historical_prices: list[float] = Field(
        default_factory=list
    )


class DiscountTruthRequest(
    PriceHistoryRequest
):
    claimed_original_price: float | None = None
    minimum_history_points: int = 3


class ConfidenceRequest(BaseModel):
    discount_truth: dict[str, Any]
    source_confidence: int
    freshness_status: str
    anomaly_detected: bool
    review_reliability: int = 50


class OpportunityListRequest(BaseModel):
    opportunities: list[dict[str, Any]] = Field(
        default_factory=list
    )


class RecommendationRequest(BaseModel):
    opportunity: dict[str, Any] = Field(
        default_factory=dict
    )


@router.post("/history")
def analyze_price_history(
    payload: PriceHistoryRequest,
):
    return PriceHistoryAnalyzer().analyze(
        **payload.model_dump()
    )


@router.post("/discount-truth")
def verify_discount_truth(
    payload: DiscountTruthRequest,
):
    return DiscountTruthEngine().verify(
        **payload.model_dump()
    )


@router.post("/confidence")
def calculate_deal_confidence(
    payload: ConfidenceRequest,
):
    return DealConfidenceEngine().calculate(
        **payload.model_dump()
    )


@router.post("/rank")
def rank_opportunities(
    payload: OpportunityListRequest,
):
    return OpportunityRanker().rank(
        opportunities=payload.opportunities
    )


@router.post("/recommendation")
def build_recommendation(
    payload: RecommendationRequest,
):
    return RecommendationBridge().build(
        opportunity=payload.opportunity
    )


@router.post("/evaluate")
def evaluate_deals(
    payload: OpportunityListRequest,
):
    return DealIntelligenceService().evaluate(
        opportunities=payload.opportunities
    )
