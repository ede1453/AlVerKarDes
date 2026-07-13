from decimal import Decimal

from app.domains.alerts.price_alert_engine import PriceAlertContext, PriceAlertEngine
from app.domains.alerts.price_alert_serializer import serialize_price_alert_decisions


def test_price_alert_engine_detects_target_price():
    decisions = PriceAlertEngine().evaluate(
        PriceAlertContext(
            current_amount=Decimal("799.00"),
            target_amount=Decimal("800.00"),
        )
    )

    assert len(decisions) == 1
    assert decisions[0].alert_type == "TARGET_PRICE"
    assert "target_price_reached" in decisions[0].reasons


def test_price_alert_engine_detects_drop_percent():
    decisions = PriceAlertEngine().evaluate(
        PriceAlertContext(
            current_amount=Decimal("850.00"),
            previous_amount=Decimal("1000.00"),
            drop_percent_threshold=Decimal("10"),
        )
    )

    assert len(decisions) == 1
    assert decisions[0].alert_type == "DROP_PERCENT"
    assert decisions[0].data["drop_percent"] == "15.00"


def test_price_alert_engine_detects_new_lowest_price():
    decisions = PriceAlertEngine().evaluate(
        PriceAlertContext(
            current_amount=Decimal("829.00"),
            previous_lowest_amount=Decimal("849.00"),
        )
    )

    assert len(decisions) == 1
    assert decisions[0].alert_type == "NEW_LOWEST_PRICE"


def test_price_alert_engine_detects_back_in_stock():
    decisions = PriceAlertEngine().evaluate(
        PriceAlertContext(
            current_amount=Decimal("849.00"),
            previous_stock_status="out_of_stock",
            current_stock_status="in_stock",
        )
    )

    assert len(decisions) == 1
    assert decisions[0].alert_type == "BACK_IN_STOCK"


def test_price_alert_engine_can_return_multiple_alerts():
    decisions = PriceAlertEngine().evaluate(
        PriceAlertContext(
            current_amount=Decimal("799.00"),
            previous_amount=Decimal("999.00"),
            target_amount=Decimal("800.00"),
            drop_percent_threshold=Decimal("10"),
            previous_lowest_amount=Decimal("849.00"),
            previous_stock_status="out_of_stock",
            current_stock_status="in_stock",
        )
    )

    alert_types = {item.alert_type for item in decisions}

    assert alert_types == {
        "TARGET_PRICE",
        "DROP_PERCENT",
        "NEW_LOWEST_PRICE",
        "BACK_IN_STOCK",
    }


def test_price_alert_serializer():
    decisions = PriceAlertEngine().evaluate(
        PriceAlertContext(
            current_amount=Decimal("799.00"),
            target_amount=Decimal("800.00"),
        )
    )

    data = serialize_price_alert_decisions(decisions)

    assert data[0]["alert_type"] == "TARGET_PRICE"
    assert data[0]["should_notify"] is True
