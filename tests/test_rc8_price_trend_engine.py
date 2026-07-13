from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.domains.analytics.price_statistics_engine import PriceStatisticsEngine
from app.domains.analytics.price_trend_engine import PriceTrendEngine


def test_price_trend_engine_detects_downward_trend():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    prices = [
        {"amount": Decimal("999.00"), "observed_at": now - timedelta(days=20)},
        {"amount": Decimal("849.00"), "observed_at": now},
    ]

    stats = PriceStatisticsEngine().calculate(prices, now=now).windows["30d"]
    trend = PriceTrendEngine().calculate(stats)

    assert trend.direction == "DOWN"
    assert trend.change_amount == Decimal("-150.00")
    assert trend.reason == "price_decreased"


def test_price_trend_engine_returns_unknown_for_insufficient_data():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    prices = [
        {"amount": Decimal("849.00"), "observed_at": now},
    ]

    stats = PriceStatisticsEngine().calculate(prices, now=now).windows["30d"]
    trend = PriceTrendEngine().calculate(stats)

    assert trend.direction == "UNKNOWN"
    assert trend.confidence == 0
