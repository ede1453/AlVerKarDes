from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from statistics import median


@dataclass
class PriceWindowStatistics:
    label: str
    window_days: int | None
    count: int
    min_amount: Decimal | None
    max_amount: Decimal | None
    average_amount: Decimal | None
    median_amount: Decimal | None
    first_amount: Decimal | None
    last_amount: Decimal | None


@dataclass
class PriceStatisticsReport:
    generated_at: datetime
    windows: dict[str, PriceWindowStatistics]


class PriceStatisticsEngine:
    DEFAULT_WINDOWS = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "180d": 180,
        "365d": 365,
        "all_time": None,
    }

    def calculate(
        self,
        prices: list,
        *,
        now: datetime | None = None,
        windows: dict[str, int | None] | None = None,
    ) -> PriceStatisticsReport:
        now = now or datetime.now(timezone.utc)
        windows = windows or self.DEFAULT_WINDOWS

        normalized = [
            item for item in prices
            if self._amount(item) is not None and self._observed_at(item) is not None
        ]
        normalized = sorted(normalized, key=lambda item: self._observed_at(item))

        return PriceStatisticsReport(
            generated_at=now,
            windows={
                label: self._calculate_window(
                    normalized,
                    label=label,
                    window_days=window_days,
                    now=now,
                )
                for label, window_days in windows.items()
            },
        )

    def _calculate_window(
        self,
        prices: list,
        *,
        label: str,
        window_days: int | None,
        now: datetime,
    ) -> PriceWindowStatistics:
        if window_days is None:
            window_prices = prices
        else:
            start = now - timedelta(days=window_days)
            window_prices = [
                item for item in prices
                if self._observed_at(item) >= start
            ]

        amounts = [self._amount(item) for item in window_prices]

        if not amounts:
            return PriceWindowStatistics(
                label=label,
                window_days=window_days,
                count=0,
                min_amount=None,
                max_amount=None,
                average_amount=None,
                median_amount=None,
                first_amount=None,
                last_amount=None,
            )

        average = sum(amounts, Decimal("0")) / Decimal(len(amounts))

        return PriceWindowStatistics(
            label=label,
            window_days=window_days,
            count=len(amounts),
            min_amount=min(amounts),
            max_amount=max(amounts),
            average_amount=average,
            median_amount=Decimal(str(median(amounts))),
            first_amount=amounts[0],
            last_amount=amounts[-1],
        )

    def _amount(self, item) -> Decimal | None:
        value = item.get("amount") if isinstance(item, dict) else getattr(item, "amount", None)
        if value is None:
            return None
        return Decimal(str(value))

    def _observed_at(self, item) -> datetime | None:
        value = item.get("observed_at", None) if isinstance(item, dict) else getattr(item, "observed_at", None)
        if value is None:
            value = item.get("created_at", None) if isinstance(item, dict) else getattr(item, "created_at", None)
        return value
