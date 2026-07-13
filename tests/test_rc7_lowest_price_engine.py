from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.domains.deals.lowest_price_engine import LowestPriceEngine
from app.domains.deals.lowest_price_serializer import serialize_lowest_price_report


def test_lowest_price_engine_calculates_windows():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)

    prices = [
        {"amount": Decimal("999.00"), "observed_at": now - timedelta(days=120)},
        {"amount": Decimal("899.00"), "observed_at": now - timedelta(days=60)},
        {"amount": Decimal("849.00"), "observed_at": now - timedelta(days=20)},
        {"amount": Decimal("879.00"), "observed_at": now - timedelta(days=2)},
    ]

    report = LowestPriceEngine().calculate(prices, now=now)

    assert report.current_amount == Decimal("879.00")
    assert report.lowest_7d.amount == Decimal("879.00")
    assert report.lowest_30d.amount == Decimal("849.00")
    assert report.lowest_90d.amount == Decimal("849.00")
    assert report.lowest_all_time.amount == Decimal("849.00")


def test_lowest_price_engine_handles_empty_prices():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)

    report = LowestPriceEngine().calculate([], now=now)

    assert report.current_amount is None
    assert report.lowest_7d.amount is None
    assert report.lowest_all_time.amount is None


def test_lowest_price_serializer_returns_strings():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)

    report = LowestPriceEngine().calculate(
        [{"amount": Decimal("879.00"), "observed_at": now}],
        now=now,
    )

    data = serialize_lowest_price_report(report)

    assert data["current_amount"] == "879.00"
    assert data["lowest_7d"]["amount"] == "879.00"
    assert data["lowest_all_time"]["observed_at"] == now.isoformat()
