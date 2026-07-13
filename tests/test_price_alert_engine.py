from decimal import Decimal

from app.domains.alerts.price_alert_engine import PriceAlertEngine, PriceAlertRule


class Price:
    def __init__(self, amount, stock_status="in_stock"):
        self.amount = amount
        self.stock_status = stock_status


class PriceChange:
    def __init__(self, direction="SAME", change_percent=Decimal("0.00")):
        self.direction = direction
        self.change_percent = change_percent


def test_target_price_alert_triggers_when_price_below_target():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="TARGET_PRICE", target_amount=Decimal("800.00")),
        current_price=Price(Decimal("799.00")),
        price_change=None,
    )

    assert result.triggered is True
    assert result.reason == "target_price_reached"


def test_target_price_alert_does_not_trigger_above_target():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="TARGET_PRICE", target_amount=Decimal("800.00")),
        current_price=Price(Decimal("849.00")),
        price_change=None,
    )

    assert result.triggered is False
    assert result.reason == "target_price_not_reached"


def test_drop_percent_alert_triggers_when_drop_reaches_threshold():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="DROP_PERCENT", drop_percent_threshold=Decimal("5.00")),
        current_price=Price(Decimal("799.00")),
        price_change=PriceChange(direction="DOWN", change_percent=Decimal("-5.89")),
    )

    assert result.triggered is True
    assert result.reason == "drop_percent_reached"


def test_drop_percent_alert_does_not_trigger_when_price_up():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="DROP_PERCENT", drop_percent_threshold=Decimal("5.00")),
        current_price=Price(Decimal("849.00")),
        price_change=PriceChange(direction="UP", change_percent=Decimal("6.26")),
    )

    assert result.triggered is False
    assert result.reason == "price_not_down"


def test_back_in_stock_alert_triggers():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="BACK_IN_STOCK", notify_on_back_in_stock=True),
        current_price=Price(Decimal("849.00"), stock_status="in_stock"),
        previous_price=Price(Decimal("849.00"), stock_status="out_of_stock"),
        price_change=None,
    )

    assert result.triggered is True
    assert result.reason == "back_in_stock"
