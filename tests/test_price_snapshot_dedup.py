from decimal import Decimal

from app.domains.market.price_dedup import PriceSnapshotDeduplicator


class Price:
    def __init__(self, amount, currency="EUR", stock_status="in_stock"):
        self.amount = amount
        self.currency = currency
        self.stock_status = stock_status


def test_price_snapshot_created_when_no_previous_price():
    decision = PriceSnapshotDeduplicator().should_create_snapshot(
        latest_price=None,
        new_amount=Decimal("849.00"),
        new_currency="EUR",
        new_stock_status="in_stock",
    )

    assert decision.should_create is True
    assert decision.reason == "no_previous_price"


def test_price_snapshot_skipped_when_same_price_currency_stock():
    decision = PriceSnapshotDeduplicator().should_create_snapshot(
        latest_price=Price(Decimal("849.00"), "EUR", "in_stock"),
        new_amount=Decimal("849.00"),
        new_currency="EUR",
        new_stock_status="in_stock",
    )

    assert decision.should_create is False
    assert decision.reason == "duplicate_price_snapshot"


def test_price_snapshot_created_when_amount_changes():
    decision = PriceSnapshotDeduplicator().should_create_snapshot(
        latest_price=Price(Decimal("849.00"), "EUR", "in_stock"),
        new_amount=Decimal("799.00"),
        new_currency="EUR",
        new_stock_status="in_stock",
    )

    assert decision.should_create is True
    assert decision.reason == "amount_changed"


def test_price_snapshot_created_when_stock_changes():
    decision = PriceSnapshotDeduplicator().should_create_snapshot(
        latest_price=Price(Decimal("849.00"), "EUR", "in_stock"),
        new_amount=Decimal("849.00"),
        new_currency="EUR",
        new_stock_status="out_of_stock",
    )

    assert decision.should_create is True
    assert decision.reason == "stock_status_changed"
