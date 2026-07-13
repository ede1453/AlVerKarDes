from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PriceTrendResult:
    direction: str
    change_amount: Decimal | None
    change_percent: Decimal | None
    confidence: int
    reason: str


class PriceTrendEngine:
    def calculate(self, stats) -> PriceTrendResult:
        if stats.count < 2 or stats.first_amount is None or stats.last_amount is None:
            return PriceTrendResult(
                direction="UNKNOWN",
                change_amount=None,
                change_percent=None,
                confidence=0,
                reason="not_enough_price_points",
            )

        change_amount = stats.last_amount - stats.first_amount

        if stats.first_amount == 0:
            change_percent = None
        else:
            change_percent = (change_amount / stats.first_amount) * Decimal("100")

        if change_amount < 0:
            direction = "DOWN"
            reason = "price_decreased"
        elif change_amount > 0:
            direction = "UP"
            reason = "price_increased"
        else:
            direction = "FLAT"
            reason = "price_unchanged"

        confidence = min(100, 40 + stats.count * 10)

        return PriceTrendResult(
            direction=direction,
            change_amount=change_amount,
            change_percent=change_percent,
            confidence=confidence,
            reason=reason,
        )
