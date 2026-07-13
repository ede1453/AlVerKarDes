from decimal import Decimal

from app.domains.market.price_change_detector import PriceChangeDetector


class Price:
    def __init__(self, amount):
        self.amount = amount


def test_price_change_detector_new_price():
    result = PriceChangeDetector().detect(
        previous_price=None,
        current_price=Price(Decimal("849.00")),
    )

    assert result.changed is False
    assert result.direction == "NEW"
    assert result.previous_amount is None
    assert result.current_amount == Decimal("849.00")


def test_price_change_detector_same_price():
    result = PriceChangeDetector().detect(
        previous_price=Price(Decimal("849.00")),
        current_price=Price(Decimal("849.00")),
    )

    assert result.changed is False
    assert result.direction == "SAME"
    assert result.change_amount == Decimal("0.00")
    assert result.change_percent == Decimal("0.00")


def test_price_change_detector_price_down():
    result = PriceChangeDetector().detect(
        previous_price=Price(Decimal("849.00")),
        current_price=Price(Decimal("799.00")),
    )

    assert result.changed is True
    assert result.direction == "DOWN"
    assert result.change_amount == Decimal("-50.00")
    assert result.change_percent == Decimal("-5.89")


def test_price_change_detector_price_up():
    result = PriceChangeDetector().detect(
        previous_price=Price(Decimal("799.00")),
        current_price=Price(Decimal("849.00")),
    )

    assert result.changed is True
    assert result.direction == "UP"
    assert result.change_amount == Decimal("50.00")
    assert result.change_percent == Decimal("6.26")
