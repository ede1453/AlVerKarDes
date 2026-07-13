from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PriceDedupDecision:
    should_create: bool
    reason: str


class PriceSnapshotDeduplicator:
    def should_create_snapshot(
        self,
        *,
        latest_price,
        new_amount,
        new_currency: str = "EUR",
        new_stock_status: str | None = None,
    ) -> PriceDedupDecision:
        if latest_price is None:
            return PriceDedupDecision(True, "no_previous_price")

        latest_amount = Decimal(str(getattr(latest_price, "amount", "")))
        incoming_amount = Decimal(str(new_amount))

        latest_currency = getattr(latest_price, "currency", "EUR")
        latest_stock = getattr(latest_price, "stock_status", None)

        if latest_amount != incoming_amount:
            return PriceDedupDecision(True, "amount_changed")

        if latest_currency != new_currency:
            return PriceDedupDecision(True, "currency_changed")

        if latest_stock != new_stock_status:
            return PriceDedupDecision(True, "stock_status_changed")

        return PriceDedupDecision(False, "duplicate_price_snapshot")
