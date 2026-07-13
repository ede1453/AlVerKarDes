from __future__ import annotations

from datetime import datetime, timezone
from statistics import median
from typing import Any


class PriceAnomalyDetector:
    def detect(
        self,
        *,
        current_price: float,
        historical_prices: list[float],
        lower_ratio: float = 0.4,
        upper_ratio: float = 2.0,
    ) -> dict[str, Any]:
        valid_history = [
            float(value)
            for value in historical_prices
            if float(value) > 0
        ]

        if current_price <= 0:
            return {
                "anomalous": True,
                "reason": "INVALID_CURRENT_PRICE",
                "reference_price": None,
            }

        if len(valid_history) < 3:
            return {
                "anomalous": False,
                "reason": "INSUFFICIENT_HISTORY",
                "reference_price": None,
            }

        reference = float(median(valid_history))
        ratio = float(current_price) / reference

        if ratio < lower_ratio:
            reason = "UNREALISTICALLY_LOW"
            anomalous = True
        elif ratio > upper_ratio:
            reason = "UNREALISTICALLY_HIGH"
            anomalous = True
        else:
            reason = "WITHIN_EXPECTED_RANGE"
            anomalous = False

        return {
            "anomalous": anomalous,
            "reason": reason,
            "reference_price": reference,
            "price_ratio": round(ratio, 4),
            "metadata": {
                "detector_version": "price_anomaly_v1"
            },
        }


class PriceFreshnessService:
    def evaluate(
        self,
        *,
        observed_at: str,
        reference_time: str | None = None,
        fresh_hours: int = 24,
        stale_hours: int = 72,
    ) -> dict[str, Any]:
        observed = datetime.fromisoformat(observed_at)
        reference = (
            datetime.fromisoformat(reference_time)
            if reference_time
            else datetime.now(timezone.utc)
        )

        age_hours = (
            reference - observed
        ).total_seconds() / 3600

        if age_hours < 0:
            status = "FUTURE_TIMESTAMP"
            usable = False
        elif age_hours <= fresh_hours:
            status = "FRESH"
            usable = True
        elif age_hours <= stale_hours:
            status = "AGING"
            usable = True
        else:
            status = "STALE"
            usable = False

        return {
            "status": status,
            "usable": usable,
            "age_hours": round(age_hours, 3),
            "metadata": {
                "freshness_version": "price_freshness_v1"
            },
        }


class CurrencyNormalizer:
    def normalize(
        self,
        *,
        amount: float,
        source_currency: str,
        target_currency: str,
        rates: dict[str, float],
    ) -> dict[str, Any]:
        source = source_currency.upper()
        target = target_currency.upper()

        if amount < 0:
            return {
                "normalized": False,
                "reason": "INVALID_AMOUNT",
                "amount": None,
            }

        if source == target:
            return {
                "normalized": True,
                "reason": "SAME_CURRENCY",
                "amount": round(float(amount), 4),
                "currency": target,
                "rate": 1.0,
            }

        pair = f"{source}_{target}"
        rate = rates.get(pair)

        if rate is None or rate <= 0:
            return {
                "normalized": False,
                "reason": "EXCHANGE_RATE_NOT_FOUND",
                "amount": None,
                "currency": target,
            }

        return {
            "normalized": True,
            "reason": "CURRENCY_CONVERTED",
            "amount": round(
                float(amount) * float(rate),
                4,
            ),
            "currency": target,
            "rate": float(rate),
            "metadata": {
                "currency_version": "currency_normalization_v1"
            },
        }


class SourceTrustReconciler:
    def reconcile(
        self,
        *,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not offers:
            return {
                "resolved": False,
                "reason": "NO_OFFERS",
                "offers": [],
            }

        reconciled = []

        for offer in offers:
            trust = min(
                max(
                    int(
                        offer.get(
                            "source_trust_score",
                            0,
                        )
                    ),
                    0,
                ),
                100,
            )

            verified = bool(
                offer.get("verified_source", False)
            )

            confidence = trust

            if verified:
                confidence = min(
                    100,
                    confidence + 10,
                )

            if offer.get("anomalous", False):
                confidence = max(
                    0,
                    confidence - 40,
                )

            reconciled.append(
                {
                    **offer,
                    "source_confidence": confidence,
                }
            )

        reconciled.sort(
            key=lambda item: (
                item["source_confidence"],
                -float(item.get("price", 0)),
            ),
            reverse=True,
        )

        return {
            "resolved": True,
            "reason": "SOURCE_TRUST_RECONCILED",
            "offers": reconciled,
            "best_source_offer": reconciled[0],
            "metadata": {
                "trust_version": "source_trust_reconciliation_v1"
            },
        }


class BestOfferAggregator:
    def select(
        self,
        *,
        offers: list[dict[str, Any]],
        minimum_source_confidence: int = 50,
    ) -> dict[str, Any]:
        eligible = []

        for offer in offers:
            if not offer.get("usable", True):
                continue

            if offer.get("anomalous", False):
                continue

            confidence = int(
                offer.get(
                    "source_confidence",
                    offer.get(
                        "source_trust_score",
                        0,
                    ),
                )
            )

            if confidence < minimum_source_confidence:
                continue

            price = float(
                offer.get("normalized_price")
                or offer.get("price")
                or 0
            )

            shipping = float(
                offer.get("shipping_cost", 0)
            )

            if price <= 0:
                continue

            effective_price = price + max(
                shipping,
                0,
            )

            eligible.append(
                {
                    **offer,
                    "effective_price": round(
                        effective_price,
                        4,
                    ),
                    "source_confidence": confidence,
                }
            )

        if not eligible:
            return {
                "selected": False,
                "reason": "NO_ELIGIBLE_OFFER",
                "best_offer": None,
                "eligible_count": 0,
            }

        eligible.sort(
            key=lambda item: (
                item["effective_price"],
                -item["source_confidence"],
            )
        )

        return {
            "selected": True,
            "reason": "BEST_OFFER_SELECTED",
            "best_offer": eligible[0],
            "eligible_count": len(eligible),
            "eligible_offers": eligible,
            "metadata": {
                "aggregation_version": "best_offer_aggregation_v1"
            },
        }


class PriceQualityPipeline:
    def __init__(self) -> None:
        self.anomaly_detector = PriceAnomalyDetector()
        self.freshness = PriceFreshnessService()
        self.currency = CurrencyNormalizer()
        self.trust = SourceTrustReconciler()
        self.aggregator = BestOfferAggregator()

    def evaluate_offers(
        self,
        *,
        offers: list[dict[str, Any]],
        target_currency: str,
        exchange_rates: dict[str, float],
        reference_time: str | None = None,
    ) -> dict[str, Any]:
        evaluated = []

        for offer in offers:
            anomaly = self.anomaly_detector.detect(
                current_price=float(offer["price"]),
                historical_prices=[
                    float(value)
                    for value in offer.get(
                        "historical_prices",
                        [],
                    )
                ],
            )

            freshness = self.freshness.evaluate(
                observed_at=offer["observed_at"],
                reference_time=reference_time,
            )

            currency = self.currency.normalize(
                amount=float(offer["price"]),
                source_currency=offer["currency"],
                target_currency=target_currency,
                rates=exchange_rates,
            )

            evaluated.append(
                {
                    **offer,
                    "anomalous": anomaly["anomalous"],
                    "anomaly_reason": anomaly["reason"],
                    "usable": freshness["usable"],
                    "freshness_status": freshness["status"],
                    "normalized_price": (
                        currency["amount"]
                        if currency["normalized"]
                        else None
                    ),
                    "normalized_currency": target_currency,
                }
            )

        trusted = self.trust.reconcile(
            offers=evaluated
        )

        if not trusted["resolved"]:
            return {
                "evaluated_count": 0,
                "result": trusted,
            }

        selection = self.aggregator.select(
            offers=trusted["offers"]
        )

        return {
            "evaluated_count": len(evaluated),
            "offers": trusted["offers"],
            "selection": selection,
            "metadata": {
                "pipeline_version": "price_quality_pipeline_v1"
            },
        }
