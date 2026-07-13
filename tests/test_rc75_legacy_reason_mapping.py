from decimal import Decimal

from app.domains.alerts.price_alert_engine import PriceAlertDecision, PriceAlertEngine, PriceAlertRule


class Price:
    def __init__(self, amount, stock_status="in_stock"):
        self.amount = amount
        self.stock_status = stock_status


class PriceChange:
    def __init__(self, direction, change_percent):
        self.direction = direction
        self.change_percent = change_percent


def test_legacy_reason_maps_drop_percent_reached():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="DROP_PERCENT", drop_percent_threshold=Decimal("5.00")),
        current_price=Price(Decimal("799.00")),
        price_change=PriceChange(direction="DOWN", change_percent=Decimal("-5.89")),
    )

    assert result.reasons == ["drop_percent_threshold_reached"]
    assert result.reason == "drop_percent_reached"


def test_legacy_reason_maps_price_not_down():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="DROP_PERCENT", drop_percent_threshold=Decimal("5.00")),
        current_price=Price(Decimal("849.00")),
        price_change=PriceChange(direction="UP", change_percent=Decimal("6.26")),
    )

    assert result.reasons == ["drop_percent_threshold_not_reached"]
    assert result.reason == "price_not_down"


def test_legacy_reason_maps_back_in_stock():
    result = PriceAlertEngine().evaluate(
        rule=PriceAlertRule(rule_type="BACK_IN_STOCK", notify_on_back_in_stock=True),
        current_price=Price(Decimal("849.00"), stock_status="in_stock"),
        previous_price=Price(Decimal("849.00"), stock_status="out_of_stock"),
        price_change=None,
    )

    assert result.reasons == ["back_in_stock_detected"]
    assert result.reason == "back_in_stock"


def test_legacy_reason_unknown_values_passthrough():
    result = PriceAlertDecision(
        should_notify=False,
        alert_type="TARGET_PRICE",
        reasons=["target_price_not_reached"],
        data={},
    )

    assert result.reason == "target_price_not_reached"
