from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.domains.analytics.price_analytics_serializer import serialize_price_statistics_report
from app.domains.analytics.price_statistics_engine import PriceStatisticsEngine
from app.domains.analytics.price_trend_engine import PriceTrendEngine


def test_price_analytics_serializer_includes_stats_and_trend():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    prices = [
        {"amount": Decimal("999.00"), "observed_at": now - timedelta(days=20)},
        {"amount": Decimal("849.00"), "observed_at": now},
    ]

    report = PriceStatisticsEngine().calculate(prices, now=now)
    trend = PriceTrendEngine().calculate(report.windows["30d"])

    data = serialize_price_statistics_report(report, {"30d": trend})

    assert data["windows"]["30d"]["min_amount"] == "849.00"
    assert data["windows"]["30d"]["trend"]["direction"] == "DOWN"
