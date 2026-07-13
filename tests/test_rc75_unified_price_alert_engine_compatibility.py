from decimal import Decimal

from app.domains.alerts.price_alert_engine import (
    PriceAlertContext,
    PriceAlertEngine,
    PriceAlertRule,
)


class Price:
    def __init__(self, amount, stock_status="in_stock"):
        self.amount = amount
        self.stock_status = stock_status


class PriceChange:
    def __init__(self, direction, change_percent):
        self.direction = direction
        self.change_percent = change_percent


def test_unified_engine_supports_keyword_rule_target_price():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="TARGET_PRICE", target_amount=Decimal("800.00")),
        current_price=Price(Decimal("799.00")),
        price_change=None,
    )

    assert result.should_notify is True
    assert result.alert_type == "TARGET_PRICE"


def test_unified_engine_supports_keyword_rule_drop_percent():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="DROP_PERCENT", drop_percent_threshold=Decimal("5.00")),
        current_price=Price(Decimal("799.00")),
        price_change=PriceChange(direction="DOWN", change_percent=Decimal("-5.89")),
    )

    assert result.should_notify is True
    assert result.alert_type == "DROP_PERCENT"


def test_unified_engine_supports_keyword_rule_back_in_stock():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="BACK_IN_STOCK", notify_on_back_in_stock=True),
        current_price=Price(Decimal("849.00"), stock_status="in_stock"),
        previous_price=Price(Decimal("849.00"), stock_status="out_of_stock"),
        price_change=None,
    )

    assert result.should_notify is True
    assert result.alert_type == "BACK_IN_STOCK"


def test_unified_engine_still_supports_rc75_context_api():
    decisions = PriceAlertEngine().evaluate(
        PriceAlertContext(
            current_amount=Decimal("799.00"),
            target_amount=Decimal("800.00"),
        )
    )

    assert len(decisions) == 1
    assert decisions[0].alert_type == "TARGET_PRICE"
