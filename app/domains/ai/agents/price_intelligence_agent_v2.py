from dataclasses import dataclass
from typing import Any

from app.domains.market.price_intelligence import PriceHistoryAnalyzer, PricePoint


@dataclass
class PriceAgentV2Input:
    prices: list[Any]


@dataclass
class PriceAgentV2Output:
    price_signal: str
    confidence: float
    current_price: float | None
    historical_lowest: float | None
    historical_average: float | None
    fake_discount_risk: str
    position_score: float
    volatility_score: float
    evidence: dict
    uncertainty: dict


class PriceIntelligenceAgentV2:
    def __init__(self):
        self.analyzer = PriceHistoryAnalyzer()

    def analyze(self, payload: PriceAgentV2Input) -> PriceAgentV2Output:
        points = self._to_price_points(payload.prices)

        if not points:
            return PriceAgentV2Output(
                price_signal="INSUFFICIENT_HISTORY",
                confidence=0,
                current_price=None,
                historical_lowest=None,
                historical_average=None,
                fake_discount_risk="UNKNOWN",
                position_score=0,
                volatility_score=0,
                evidence={
                    "type": "PRICE_HISTORY",
                    "title": "No price history",
                    "data": {"history_points": 0},
                    "confidence": 0,
                },
                uncertainty={
                    "level": "HIGH",
                    "explanation": "No price history is available.",
                },
            )

        result = self.analyzer.analyze(points)

        uncertainty_level = "LOW"
        if result.history_points < 5:
            uncertainty_level = "HIGH"
        elif result.fake_discount_risk in {"HIGH", "UNKNOWN"}:
            uncertainty_level = "MEDIUM"

        return PriceAgentV2Output(
            price_signal=result.signal,
            confidence=result.confidence,
            current_price=result.current_price,
            historical_lowest=result.historical_lowest,
            historical_average=result.historical_average,
            fake_discount_risk=result.fake_discount_risk,
            position_score=result.position_score,
            volatility_score=result.volatility_score,
            evidence={
                "type": "PRICE_HISTORY",
                "title": "Historical price intelligence",
                "data": {
                    "current_price": result.current_price,
                    "historical_lowest": result.historical_lowest,
                    "historical_highest": result.historical_highest,
                    "historical_average": result.historical_average,
                    "history_points": result.history_points,
                    "discount_from_average_pct": result.discount_from_average_pct,
                    "position_score": result.position_score,
                    "volatility_score": result.volatility_score,
                    "fake_discount_risk": result.fake_discount_risk,
                    "currency": result.currency,
                },
                "confidence": result.confidence,
            },
            uncertainty={
                "level": uncertainty_level,
                "explanation": result.explanation,
            },
        )

    def _to_price_points(self, prices: list[Any]) -> list[PricePoint]:
        points: list[PricePoint] = []

        for price in prices:
            amount = self._read(price, "amount")
            currency = self._read(price, "currency") or "EUR"
            observed_at = self._read(price, "observed_at") or self._read(price, "created_at")

            if amount is None:
                continue

            points.append(
                PricePoint(
                    amount=float(amount),
                    currency=str(currency),
                    observed_at=str(observed_at) if observed_at else None,
                )
            )

        return points

    def _read(self, obj: Any, key: str):
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)
