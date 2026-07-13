from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal


@dataclass
class LowestPricePoint:
    amount: Decimal | None
    observed_at: datetime | None
    window_days: int | None
    label: str


@dataclass
class LowestPriceReport:
    current_amount: Decimal | None
    lowest_7d: LowestPricePoint
    lowest_30d: LowestPricePoint
    lowest_90d: LowestPricePoint
    lowest_all_time: LowestPricePoint


class LowestPriceEngine:
    def calculate(self, prices: list, now: datetime | None = None) -> LowestPriceReport:
        now = now or datetime.now(timezone.utc)
        sorted_prices = sorted(prices, key=lambda item: self._observed_at(item) or now)

        current_amount = None
        if sorted_prices:
            current_amount = self._amount(sorted_prices[-1])

        return LowestPriceReport(
            current_amount=current_amount,
            lowest_7d=self._lowest_in_window(sorted_prices, now, 7, "lowest_7d"),
            lowest_30d=self._lowest_in_window(sorted_prices, now, 30, "lowest_30d"),
            lowest_90d=self._lowest_in_window(sorted_prices, now, 90, "lowest_90d"),
            lowest_all_time=self._lowest_all_time(sorted_prices),
        )

    def _lowest_in_window(self, prices: list, now: datetime, days: int, label: str) -> LowestPricePoint:
        start = now - timedelta(days=days)
        window_prices = [
            item for item in prices
            if self._observed_at(item) and self._observed_at(item) >= start
        ]
        return self._lowest(window_prices, window_days=days, label=label)

    def _lowest_all_time(self, prices: list) -> LowestPricePoint:
        return self._lowest(prices, window_days=None, label="lowest_all_time")

    def _lowest(self, prices: list, window_days: int | None, label: str) -> LowestPricePoint:
        if not prices:
            return LowestPricePoint(
                amount=None,
                observed_at=None,
                window_days=window_days,
                label=label,
            )

        lowest = min(prices, key=lambda item: self._amount(item))
        return LowestPricePoint(
            amount=self._amount(lowest),
            observed_at=self._observed_at(lowest),
            window_days=window_days,
            label=label,
        )

    def _amount(self, item) -> Decimal:
        value = item.get("amount") if isinstance(item, dict) else item.amount
        return Decimal(str(value))

    def _observed_at(self, item) -> datetime | None:
        value = item.get("observed_at", None) if isinstance(item, dict) else getattr(item, "observed_at", None)
        if value is None:
            value = item.get("created_at", None) if isinstance(item, dict) else getattr(item, "created_at", None)
        return value
