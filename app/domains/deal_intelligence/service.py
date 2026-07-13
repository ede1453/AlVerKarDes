from __future__ import annotations

from statistics import mean, median
from typing import Any


class PriceHistoryAnalyzer:
    def analyze(
        self,
        *,
        current_price: float,
        historical_prices: list[float],
    ) -> dict[str, Any]:
        history = [
            float(value)
            for value in historical_prices
            if float(value) > 0
        ]

        if current_price <= 0:
            return {
                "analyzed": False,
                "reason": "INVALID_CURRENT_PRICE",
            }

        if not history:
            return {
                "analyzed": False,
                "reason": "NO_PRICE_HISTORY",
                "current_price": float(current_price),
                "history_count": 0,
            }

        average_price = mean(history)
        median_price = median(history)
        lowest_price = min(history)
        highest_price = max(history)

        discount_vs_average = (
            (average_price - current_price)
            / average_price
            * 100
        )

        discount_vs_median = (
            (median_price - current_price)
            / median_price
            * 100
        )

        distance_from_low = (
            (current_price - lowest_price)
            / lowest_price
            * 100
        )

        return {
            "analyzed": True,
            "reason": "PRICE_HISTORY_ANALYZED",
            "current_price": float(current_price),
            "history_count": len(history),
            "average_price": round(average_price, 4),
            "median_price": round(median_price, 4),
            "lowest_price": round(lowest_price, 4),
            "highest_price": round(highest_price, 4),
            "discount_vs_average_pct": round(
                discount_vs_average,
                2,
            ),
            "discount_vs_median_pct": round(
                discount_vs_median,
                2,
            ),
            "distance_from_low_pct": round(
                distance_from_low,
                2,
            ),
            "metadata": {
                "analysis_version": "price_history_analysis_v1"
            },
        }


class DiscountTruthEngine:
    def verify(
        self,
        *,
        current_price: float,
        claimed_original_price: float | None,
        historical_prices: list[float],
        minimum_history_points: int = 3,
    ) -> dict[str, Any]:
        analyzer = PriceHistoryAnalyzer()
        analysis = analyzer.analyze(
            current_price=current_price,
            historical_prices=historical_prices,
        )

        if not analysis["analyzed"]:
            return {
                "verified": False,
                "truth_status": "INSUFFICIENT_DATA",
                "reason": analysis["reason"],
                "analysis": analysis,
            }

        if analysis["history_count"] < minimum_history_points:
            return {
                "verified": False,
                "truth_status": "INSUFFICIENT_DATA",
                "reason": "NOT_ENOUGH_HISTORY_POINTS",
                "analysis": analysis,
            }

        claimed_discount = None

        if (
            claimed_original_price is not None
            and claimed_original_price > 0
        ):
            claimed_discount = (
                (
                    claimed_original_price
                    - current_price
                )
                / claimed_original_price
                * 100
            )

        observed_discount = analysis[
            "discount_vs_median_pct"
        ]

        if observed_discount >= 25:
            truth_status = "GENUINE_STRONG_DISCOUNT"
            verified = True
        elif observed_discount >= 10:
            truth_status = "GENUINE_MODERATE_DISCOUNT"
            verified = True
        elif observed_discount > 0:
            truth_status = "SMALL_DISCOUNT"
            verified = True
        else:
            truth_status = "NO_REAL_DISCOUNT"
            verified = False

        misleading = (
            claimed_discount is not None
            and claimed_discount - observed_discount >= 15
        )

        if misleading:
            truth_status = "POSSIBLY_MISLEADING_DISCOUNT"
            verified = False

        return {
            "verified": verified,
            "truth_status": truth_status,
            "claimed_discount_pct": (
                round(claimed_discount, 2)
                if claimed_discount is not None
                else None
            ),
            "observed_discount_pct": observed_discount,
            "misleading_claim": misleading,
            "analysis": analysis,
            "metadata": {
                "truth_version": "discount_truth_v1"
            },
        }


class DealConfidenceEngine:
    def calculate(
        self,
        *,
        discount_truth: dict[str, Any],
        source_confidence: int,
        freshness_status: str,
        anomaly_detected: bool,
        review_reliability: int = 50,
    ) -> dict[str, Any]:
        score = 0.0
        reasons: list[str] = []

        truth_status = discount_truth.get(
            "truth_status",
            "INSUFFICIENT_DATA",
        )

        truth_scores = {
            "GENUINE_STRONG_DISCOUNT": 40,
            "GENUINE_MODERATE_DISCOUNT": 30,
            "SMALL_DISCOUNT": 15,
            "NO_REAL_DISCOUNT": 0,
            "POSSIBLY_MISLEADING_DISCOUNT": -20,
            "INSUFFICIENT_DATA": 5,
        }

        score += truth_scores.get(
            truth_status,
            0,
        )
        reasons.append(truth_status)

        bounded_source = min(
            max(int(source_confidence), 0),
            100,
        )
        score += bounded_source * 0.3
        reasons.append(
            f"SOURCE_CONFIDENCE_{bounded_source}"
        )

        freshness_scores = {
            "FRESH": 15,
            "AGING": 7,
            "STALE": -10,
            "FUTURE_TIMESTAMP": -20,
        }

        score += freshness_scores.get(
            freshness_status,
            0,
        )
        reasons.append(
            f"FRESHNESS_{freshness_status}"
        )

        bounded_review = min(
            max(int(review_reliability), 0),
            100,
        )
        score += bounded_review * 0.15

        if anomaly_detected:
            score -= 35
            reasons.append("PRICE_ANOMALY_PENALTY")

        final_score = round(
            min(max(score, 0.0), 100.0),
            2,
        )

        if final_score >= 80:
            level = "VERY_HIGH"
        elif final_score >= 65:
            level = "HIGH"
        elif final_score >= 50:
            level = "MEDIUM"
        elif final_score >= 30:
            level = "LOW"
        else:
            level = "VERY_LOW"

        return {
            "confidence_score": final_score,
            "confidence_level": level,
            "reasons": reasons,
            "metadata": {
                "confidence_version": "deal_confidence_v1"
            },
        }


class OpportunityRanker:
    def rank(
        self,
        *,
        opportunities: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ranked = []

        for opportunity in opportunities:
            confidence = float(
                opportunity.get(
                    "confidence_score",
                    0,
                )
            )

            discount = float(
                opportunity.get(
                    "observed_discount_pct",
                    0,
                )
            )

            source_trust = float(
                opportunity.get(
                    "source_confidence",
                    0,
                )
            )

            effective_price = float(
                opportunity.get(
                    "effective_price",
                    opportunity.get("price", 0),
                )
            )

            score = (
                confidence * 0.55
                + max(discount, 0) * 0.3
                + source_trust * 0.15
            )

            ranked.append(
                {
                    **opportunity,
                    "opportunity_score": round(
                        min(score, 100),
                        2,
                    ),
                    "effective_price": effective_price,
                }
            )

        ranked.sort(
            key=lambda item: (
                item["opportunity_score"],
                -item["effective_price"],
            ),
            reverse=True,
        )

        return {
            "ranked_count": len(ranked),
            "opportunities": ranked,
            "best_opportunity": (
                ranked[0]
                if ranked
                else None
            ),
            "metadata": {
                "ranking_version": "opportunity_ranking_v1"
            },
        }


class RecommendationBridge:
    def build(
        self,
        *,
        opportunity: dict[str, Any],
    ) -> dict[str, Any]:
        confidence = float(
            opportunity.get(
                "confidence_score",
                0,
            )
        )

        truth_status = opportunity.get(
            "truth_status",
            "INSUFFICIENT_DATA",
        )

        anomaly = bool(
            opportunity.get(
                "anomaly_detected",
                False,
            )
        )

        if anomaly:
            decision = "DO_NOT_BUY"
            summary = "Fiyat anomalisi tespit edildi."
        elif truth_status == "POSSIBLY_MISLEADING_DISCOUNT":
            decision = "DO_NOT_BUY"
            summary = "İndirim iddiası güvenilir görünmüyor."
        elif confidence >= 70 and truth_status in {
            "GENUINE_STRONG_DISCOUNT",
            "GENUINE_MODERATE_DISCOUNT",
        }:
            decision = "BUY"
            summary = "Doğrulanmış ve güvenilir fiyat fırsatı."
        elif confidence >= 45:
            decision = "WAIT"
            summary = "Fırsat mevcut ancak güven seviyesi sınırlı."
        else:
            decision = "INSUFFICIENT_DATA"
            summary = "Karar için yeterli güvenilir veri yok."

        return {
            "decision": decision,
            "confidence": round(confidence, 2),
            "summary": summary,
            "truth_status": truth_status,
            "source_id": opportunity.get("source_id"),
            "product_key": opportunity.get(
                "canonical_product_key"
            ),
            "effective_price": opportunity.get(
                "effective_price",
                opportunity.get("price"),
            ),
            "evidence": {
                "observed_discount_pct": opportunity.get(
                    "observed_discount_pct"
                ),
                "source_confidence": opportunity.get(
                    "source_confidence"
                ),
                "freshness_status": opportunity.get(
                    "freshness_status"
                ),
                "anomaly_detected": anomaly,
            },
            "metadata": {
                "bridge_version": "recommendation_bridge_v1"
            },
        }


class DealIntelligenceService:
    def __init__(self) -> None:
        self.history = PriceHistoryAnalyzer()
        self.truth = DiscountTruthEngine()
        self.confidence = DealConfidenceEngine()
        self.ranker = OpportunityRanker()
        self.bridge = RecommendationBridge()

    def evaluate(
        self,
        *,
        opportunities: list[dict[str, Any]],
    ) -> dict[str, Any]:
        evaluated = []

        for item in opportunities:
            truth = self.truth.verify(
                current_price=float(item["price"]),
                claimed_original_price=item.get(
                    "claimed_original_price"
                ),
                historical_prices=item.get(
                    "historical_prices",
                    [],
                ),
            )

            confidence = self.confidence.calculate(
                discount_truth=truth,
                source_confidence=int(
                    item.get(
                        "source_confidence",
                        0,
                    )
                ),
                freshness_status=item.get(
                    "freshness_status",
                    "STALE",
                ),
                anomaly_detected=bool(
                    item.get(
                        "anomaly_detected",
                        False,
                    )
                ),
                review_reliability=int(
                    item.get(
                        "review_reliability",
                        50,
                    )
                ),
            )

            evaluated.append(
                {
                    **item,
                    "truth_status": truth[
                        "truth_status"
                    ],
                    "observed_discount_pct": truth.get(
                        "observed_discount_pct",
                        0,
                    ),
                    "confidence_score": confidence[
                        "confidence_score"
                    ],
                    "confidence_level": confidence[
                        "confidence_level"
                    ],
                }
            )

        ranked = self.ranker.rank(
            opportunities=evaluated
        )

        recommendation = (
            self.bridge.build(
                opportunity=ranked[
                    "best_opportunity"
                ]
            )
            if ranked["best_opportunity"]
            else None
        )

        return {
            "evaluated_count": len(evaluated),
            "ranking": ranked,
            "recommendation": recommendation,
            "metadata": {
                "service_version": "deal_intelligence_v1"
            },
        }
