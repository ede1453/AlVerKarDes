from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.domains.deals.deal_summary_service import DealSummaryService


def test_deal_summary_service_returns_buy_summary():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    prices = [
        {"amount": Decimal("899.00"), "observed_at": now - timedelta(days=20)},
        {"amount": Decimal("849.00"), "observed_at": now},
    ]

    result = DealSummaryService().summarize(
        prices=prices,
        cross_store_min_amount=Decimal("849.00"),
        store_trust_score=95,
        stock_status="in_stock",
        now=now,
    )

    assert result["has_price_data"] is True
    assert result["recommendation"] == "BUY"
    assert result["deal_score"]["decision"] == "BUY"
    assert result["lowest_prices"]["lowest_30d"]["amount"] == "849.00"


def test_deal_summary_service_returns_no_price_data():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)

    result = DealSummaryService().summarize(prices=[], now=now)

    assert result["has_price_data"] is False
    assert result["deal_score"] is None
    assert result["recommendation"] == "NO_PRICE_DATA"


def test_deal_summary_service_returns_wait_summary():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    prices = [
        {"amount": Decimal("849.00"), "observed_at": now - timedelta(days=20)},
        {"amount": Decimal("999.00"), "observed_at": now},
    ]

    result = DealSummaryService().summarize(
        prices=prices,
        cross_store_min_amount=Decimal("879.00"),
        store_trust_score=40,
        stock_status="out_of_stock",
        now=now,
    )

    assert result["recommendation"] == "WAIT"
    assert result["deal_score"]["score"] < 60
