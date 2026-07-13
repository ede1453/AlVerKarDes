from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.domains.analytics.price_statistics_engine import PriceStatisticsEngine


def test_price_statistics_engine_calculates_standard_windows():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    prices = [
        {"amount": Decimal("999.00"), "observed_at": now - timedelta(days=300)},
        {"amount": Decimal("899.00"), "observed_at": now - timedelta(days=60)},
        {"amount": Decimal("849.00"), "observed_at": now - timedelta(days=20)},
        {"amount": Decimal("879.00"), "observed_at": now - timedelta(days=2)},
    ]

    report = PriceStatisticsEngine().calculate(prices, now=now)

    assert report.windows["7d"].count == 1
    assert report.windows["7d"].min_amount == Decimal("879.00")

    assert report.windows["30d"].count == 2
    assert report.windows["30d"].min_amount == Decimal("849.00")
    assert report.windows["30d"].max_amount == Decimal("879.00")

    assert report.windows["365d"].count == 4
    assert report.windows["all_time"].count == 4


def test_price_statistics_engine_handles_empty_prices():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)

    report = PriceStatisticsEngine().calculate([], now=now)

    assert report.windows["30d"].count == 0
    assert report.windows["30d"].min_amount is None
    assert report.windows["all_time"].average_amount is None
