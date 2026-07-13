from decimal import Decimal

from app.domains.alerts.price_alert_engine import (
    PriceAlertContext,
    PriceAlertEngine,
    PriceAlertRule,
)


def test_price_alert_rule_import_is_backward_compatible():
    rule = PriceAlertRule(
        rule_type="TARGET_PRICE",
        target_amount=Decimal("800.00"),
    )

    assert rule.rule_type == "TARGET_PRICE"
    assert rule.target_amount == Decimal("800.00")


def test_engine_can_evaluate_legacy_target_price_rule():
    rule = PriceAlertRule(
        rule_type="TARGET_PRICE",
        target_amount=Decimal("800.00"),
    )

    decision = PriceAlertEngine().evaluate(
        rule,
        current_amount=Decimal("799.00"),
    )

    assert decision.should_notify is True
    assert decision.alert_type == "TARGET_PRICE"


def test_engine_can_evaluate_legacy_rule_with_context():
    rule = PriceAlertRule(
        rule_type="DROP_PERCENT",
        drop_percent_threshold=Decimal("10"),
    )

    decision = PriceAlertEngine().evaluate(
        rule,
        context=PriceAlertContext(
            current_amount=Decimal("850.00"),
            previous_amount=Decimal("1000.00"),
        ),
    )

    assert decision.should_notify is True
    assert decision.alert_type == "DROP_PERCENT"
