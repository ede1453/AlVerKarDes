from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.commerce_ingestion.price_quality import (
    BestOfferAggregator,
    CurrencyNormalizer,
    PriceAnomalyDetector,
    PriceFreshnessService,
    PriceQualityPipeline,
    SourceTrustReconciler,
)

router = APIRouter(
    prefix="/price-quality",
    tags=["price-quality"],
)


class AnomalyRequest(BaseModel):
    current_price: float
    historical_prices: list[float] = Field(
        default_factory=list
    )
    lower_ratio: float = 0.4
    upper_ratio: float = 2.0


class FreshnessRequest(BaseModel):
    observed_at: str
    reference_time: str | None = None
    fresh_hours: int = 24
    stale_hours: int = 72


class CurrencyRequest(BaseModel):
    amount: float
    source_currency: str
    target_currency: str
    rates: dict[str, float] = Field(
        default_factory=dict
    )


class OfferListRequest(BaseModel):
    offers: list[dict[str, Any]] = Field(
        default_factory=list
    )


class BestOfferRequest(OfferListRequest):
    minimum_source_confidence: int = 50


class PipelineRequest(OfferListRequest):
    target_currency: str
    exchange_rates: dict[str, float] = Field(
        default_factory=dict
    )
    reference_time: str | None = None


@router.post("/anomaly")
def detect_price_anomaly(
    payload: AnomalyRequest,
):
    return PriceAnomalyDetector().detect(
        **payload.model_dump()
    )


@router.post("/freshness")
def evaluate_price_freshness(
    payload: FreshnessRequest,
):
    return PriceFreshnessService().evaluate(
        **payload.model_dump()
    )


@router.post("/currency")
def normalize_currency(
    payload: CurrencyRequest,
):
    return CurrencyNormalizer().normalize(
        **payload.model_dump()
    )


@router.post("/reconcile")
def reconcile_sources(
    payload: OfferListRequest,
):
    return SourceTrustReconciler().reconcile(
        offers=payload.offers
    )


@router.post("/best-offer")
def select_best_offer(
    payload: BestOfferRequest,
):
    return BestOfferAggregator().select(
        offers=payload.offers,
        minimum_source_confidence=(
            payload.minimum_source_confidence
        ),
    )


@router.post("/pipeline")
def evaluate_price_quality_pipeline(
    payload: PipelineRequest,
):
    return PriceQualityPipeline().evaluate_offers(
        offers=payload.offers,
        target_currency=payload.target_currency,
        exchange_rates=payload.exchange_rates,
        reference_time=payload.reference_time,
    )
