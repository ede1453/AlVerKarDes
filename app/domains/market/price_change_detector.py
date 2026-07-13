from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass
class PriceChangeResult:
    changed: bool
    direction: str
    previous_amount: Decimal | None
    current_amount: Decimal
    change_amount: Decimal
    change_percent: Decimal


class PriceChangeDetector:
    def detect(self, *, previous_price, current_price) -> PriceChangeResult:
        current_amount = Decimal(str(current_price.amount))

        if previous_price is None:
            return PriceChangeResult(
                changed=False,
                direction="NEW",
                previous_amount=None,
                current_amount=current_amount,
                change_amount=Decimal("0.00"),
                change_percent=Decimal("0.00"),
            )

        previous_amount = Decimal(str(previous_price.amount))
        change_amount = current_amount - previous_amount

        if change_amount > 0:
            direction = "UP"
            changed = True
        elif change_amount < 0:
            direction = "DOWN"
            changed = True
        else:
            direction = "SAME"
            changed = False

        if previous_amount == 0:
            change_percent = Decimal("0.00")
        else:
            change_percent = ((change_amount / previous_amount) * Decimal("100")).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

        return PriceChangeResult(
            changed=changed,
            direction=direction,
            previous_amount=previous_amount,
            current_amount=current_amount,
            change_amount=change_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            change_percent=change_percent,
        )
