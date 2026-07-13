from dataclasses import dataclass
from decimal import Decimal


@dataclass
class DealScoreInput:
    current_amount: Decimal
    lowest_30d_amount: Decimal | None = None
    lowest_90d_amount: Decimal | None = None
    all_time_low_amount: Decimal | None = None
    cross_store_min_amount: Decimal | None = None
    store_trust_score: float | None = None
    stock_status: str | None = "in_stock"


@dataclass
class DealScoreResult:
    score: int
    decision: str
    reasons: list[str]


class DealScoreEngine:
    def calculate(self, payload: DealScoreInput) -> DealScoreResult:
        score = 50
        reasons: list[str] = []

        score += self._historical_discount_score(payload, reasons)
        score += self._cross_store_score(payload, reasons)
        score += self._trust_score(payload, reasons)
        score += self._stock_score(payload, reasons)

        score = max(0, min(100, score))

        if score >= 80:
            decision = "BUY"
        elif score >= 60:
            decision = "WATCH"
        else:
            decision = "WAIT"

        return DealScoreResult(score=score, decision=decision, reasons=reasons)

    def _historical_discount_score(self, payload: DealScoreInput, reasons: list[str]) -> int:
        reference = payload.lowest_90d_amount or payload.lowest_30d_amount or payload.all_time_low_amount
        if reference is None:
            reasons.append("historical_reference_missing")
            return 0

        current = payload.current_amount
        if current <= reference:
            reasons.append("at_or_below_historical_low")
            return 25

        gap_percent = ((current - reference) / reference) * Decimal("100")

        if gap_percent <= Decimal("3"):
            reasons.append("near_historical_low")
            return 18

        if gap_percent <= Decimal("8"):
            reasons.append("moderately_above_historical_low")
            return 8

        reasons.append("far_above_historical_low")
        return -12

    def _cross_store_score(self, payload: DealScoreInput, reasons: list[str]) -> int:
        if payload.cross_store_min_amount is None:
            reasons.append("cross_store_reference_missing")
            return 0

        if payload.current_amount <= payload.cross_store_min_amount:
            reasons.append("best_cross_store_price")
            return 15

        gap_percent = ((payload.current_amount - payload.cross_store_min_amount) / payload.cross_store_min_amount) * Decimal("100")

        if gap_percent <= Decimal("3"):
            reasons.append("near_best_cross_store_price")
            return 5

        reasons.append("not_best_cross_store_price")
        return 0

    def _trust_score(self, payload: DealScoreInput, reasons: list[str]) -> int:
        if payload.store_trust_score is None:
            reasons.append("store_trust_missing")
            return 0

        if payload.store_trust_score >= 85:
            reasons.append("high_store_trust")
            return 8

        if payload.store_trust_score >= 60:
            reasons.append("medium_store_trust")
            return 0

        reasons.append("low_store_trust")
        return -15

    def _stock_score(self, payload: DealScoreInput, reasons: list[str]) -> int:
        status = (payload.stock_status or "").lower()

        if status in {"in_stock", "available"}:
            reasons.append("in_stock")
            return 2

        if status in {"out_of_stock", "sold_out"}:
            reasons.append("out_of_stock")
            return -25

        reasons.append("stock_unknown")
        return -5
