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


def test_unified_engine_legacy_result_has_triggered_reason_message():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="TARGET_PRICE", target_amount=Decimal("800.00")),
        current_price=Price(Decimal("799.00")),
        price_change=None,
    )

    assert result.triggered is True
    assert result.reason == "target_price_reached"
    assert isinstance(result.message, str)


def test_unified_engine_legacy_drop_percent_contract():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="DROP_PERCENT", drop_percent_threshold=Decimal("5.00")),
        current_price=Price(Decimal("799.00")),
        price_change=PriceChange(direction="DOWN", change_percent=Decimal("-5.89")),
    )

    assert result.triggered is True

    # Legacy contract:
    assert result.reason == "drop_percent_reached"

    # RC7.5 richer internal reason list remains preserved:
    assert result.reasons == ["drop_percent_threshold_reached"]

    assert result.message == "Price drop threshold reached."


def test_unified_engine_context_result_still_has_new_fields():
    decisions = PriceAlertEngine().evaluate(
        PriceAlertContext(
            current_amount=Decimal("799.00"),
            target_amount=Decimal("800.00"),
        )
    )

    assert decisions[0].should_notify is True
    assert decisions[0].alert_type == "TARGET_PRICE"
    assert decisions[0].reasons == ["target_price_reached"]
