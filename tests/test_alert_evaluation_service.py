from decimal import Decimal
from uuid import uuid4

import pytest

from app.domains.alerts.evaluation_service import AlertEvaluationService


class Rule:
    def __init__(self, rule_type, offer_id, target_amount=None, drop_percent_threshold=None, notify_on_back_in_stock=False):
        self.id = uuid4()
        self.offer_id = offer_id
        self.rule_type = rule_type
        self.target_amount = target_amount
        self.drop_percent_threshold = drop_percent_threshold
        self.notify_on_back_in_stock = notify_on_back_in_stock


class FakeRuleRepository:
    def __init__(self, rules):
        self.rules = rules

    async def list_active_for_offer(self, offer_id):
        return [rule for rule in self.rules if rule.offer_id == offer_id]


class Price:
    def __init__(self, amount, stock_status="in_stock"):
        self.amount = amount
        self.stock_status = stock_status


class PriceChange:
    def __init__(self, direction="SAME", change_percent=Decimal("0.00")):
        self.direction = direction
        self.change_percent = change_percent


@pytest.mark.asyncio
async def test_alert_evaluation_service_triggers_target_price():
    offer_id = uuid4()
    service = AlertEvaluationService(
        FakeRuleRepository([
            Rule("TARGET_PRICE", offer_id, target_amount=Decimal("800.00"))
        ])
    )

    result = await service.evaluate_for_offer(
        offer_id=offer_id,
        current_price=Price(Decimal("799.00")),
    )

    assert result["evaluated_count"] == 1
    assert result["triggered_count"] == 1
    assert result["results"][0]["reason"] == "target_price_reached"


@pytest.mark.asyncio
async def test_alert_evaluation_service_triggers_drop_percent():
    offer_id = uuid4()
    service = AlertEvaluationService(
        FakeRuleRepository([
            Rule("DROP_PERCENT", offer_id, drop_percent_threshold=Decimal("5.00"))
        ])
    )

    result = await service.evaluate_for_offer(
        offer_id=offer_id,
        current_price=Price(Decimal("799.00")),
        price_change=PriceChange(direction="DOWN", change_percent=Decimal("-5.89")),
    )

    assert result["triggered_count"] == 1
    assert result["results"][0]["reason"] == "drop_percent_reached"


@pytest.mark.asyncio
async def test_alert_evaluation_service_ignores_other_offer_rules():
    offer_id = uuid4()
    other_offer_id = uuid4()
    service = AlertEvaluationService(
        FakeRuleRepository([
            Rule("TARGET_PRICE", other_offer_id, target_amount=Decimal("800.00"))
        ])
    )

    result = await service.evaluate_for_offer(
        offer_id=offer_id,
        current_price=Price(Decimal("799.00")),
    )

    assert result["evaluated_count"] == 0
    assert result["triggered_count"] == 0
