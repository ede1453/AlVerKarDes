from uuid import UUID, uuid4

import pytest

from app.domains.alerts.alert_notification_service import AlertNotificationService


class DummyDB:
    pass


class Rule:
    def __init__(self):
        self.id = uuid4()
        self.offer_id = uuid4()
        self.rule_type = "TARGET_PRICE"


class FakeQueue:
    def __init__(self):
        self.items = []

    async def enqueue(self, payload):
        item = {
            "id": str(uuid4()),
            **payload,
        }
        self.items.append(item)
        return item


class FakeCreateQueue:
    def __init__(self):
        self.items = []

    async def create(self, **payload):
        item = {
            "id": str(uuid4()),
            **payload,
        }
        self.items.append(item)
        return item


class FakeEvaluationService:
    def __init__(self, result):
        self.result = result

    async def evaluate_for_offer(self, *, offer_id, current_price, previous_price=None, price_change=None):
        return self.result


@pytest.mark.asyncio
async def test_legacy_enqueue_triggered_evaluations_queues_triggered_items():
    rule = Rule()
    service = AlertNotificationService(DummyDB())
    service.queue = FakeQueue()

    evaluations = {
        "evaluated_count": 2,
        "triggered_count": 1,
        "results": [
            {
                "rule_id": str(rule.id),
                "triggered": True,
                "message": "Price reached target.",
            },
            {
                "rule_id": str(uuid4()),
                "triggered": False,
                "message": "Not triggered.",
            },
        ],
    }

    result = await service.enqueue_triggered_evaluations(
        evaluations=evaluations,
        rules_by_id={str(rule.id): rule},
    )

    assert result["queued_count"] == 1
    assert result["skipped_untriggered_count"] == 1

    # Domain service preserves native UUID types.
    assert service.queue.items[0]["rule_id"] == rule.id
    assert isinstance(service.queue.items[0]["rule_id"], UUID)
    assert service.queue.items[0]["message"] == "Price reached target."


@pytest.mark.asyncio
async def test_legacy_enqueue_triggered_evaluations_skips_missing_rule():
    service = AlertNotificationService(DummyDB())
    service.queue = FakeQueue()

    evaluations = {
        "evaluated_count": 1,
        "triggered_count": 1,
        "results": [
            {
                "rule_id": str(uuid4()),
                "triggered": True,
                "message": "Price reached target.",
            }
        ],
    }

    result = await service.enqueue_triggered_evaluations(
        evaluations=evaluations,
        rules_by_id={},
    )

    assert result["queued_count"] == 0
    assert result["skipped_missing_rule_count"] == 1
    assert service.queue.items == []


@pytest.mark.asyncio
async def test_queue_contract_supports_create_kwargs():
    rule = Rule()
    service = AlertNotificationService(DummyDB())
    service.queue = FakeCreateQueue()

    evaluations = {
        "evaluated_count": 1,
        "triggered_count": 1,
        "results": [
            {
                "rule_id": str(rule.id),
                "triggered": True,
                "message": "Price reached target.",
            }
        ],
    }

    result = await service.enqueue_triggered_evaluations(
        evaluations=evaluations,
        rules_by_id={str(rule.id): rule},
    )

    assert result["queued_count"] == 1
    assert service.queue.items[0]["status"] == "PENDING"
    assert service.queue.items[0]["rule_id"] == rule.id


@pytest.mark.asyncio
async def test_explicit_evaluate_and_enqueue_still_works():
    offer_id = uuid4()
    rule_id = uuid4()
    queue = FakeQueue()

    service = AlertNotificationService(
        FakeEvaluationService(
            {
                "evaluated_count": 1,
                "triggered_count": 1,
                "results": [
                    {
                        "rule_id": rule_id,
                        "offer_id": offer_id,
                        "rule_type": "TARGET_PRICE",
                        "triggered": True,
                        "reason": "target_price_reached",
                        "message": "Target price reached.",
                    }
                ],
            }
        ),
        queue,
    )

    result = await service.evaluate_and_enqueue(
        offer_id=offer_id,
        current_price=object(),
    )

    assert result["queued_count"] == 1
