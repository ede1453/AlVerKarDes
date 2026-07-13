from uuid import UUID, uuid4

import pytest

from app.domains.alerts.alert_notification_service import AlertNotificationService


class DummyDB:
    pass


class Rule:
    def __init__(self):
        self.id = uuid4()
        self.offer_id = uuid4()
        self.user_id = uuid4()
        self.rule_type = "TARGET_PRICE"


class FakeQueue:
    def __init__(self):
        self.items = []


@pytest.mark.asyncio
async def test_legacy_queue_preserves_uuid_types():
    rule = Rule()
    service = AlertNotificationService(DummyDB())
    service.queue = FakeQueue()

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
    assert service.queue.items[0]["rule_id"] == rule.id
    assert isinstance(service.queue.items[0]["rule_id"], UUID)
    assert service.queue.items[0]["offer_id"] == rule.offer_id
    assert service.queue.items[0]["user_id"] == rule.user_id


@pytest.mark.asyncio
async def test_rules_by_id_accepts_uuid_key_too():
    rule = Rule()
    service = AlertNotificationService(DummyDB())
    service.queue = FakeQueue()

    evaluations = {
        "evaluated_count": 1,
        "triggered_count": 1,
        "results": [
            {
                "rule_id": rule.id,
                "triggered": True,
                "message": "Price reached target.",
            }
        ],
    }

    result = await service.enqueue_triggered_evaluations(
        evaluations=evaluations,
        rules_by_id={rule.id: rule},
    )

    assert result["queued_count"] == 1
    assert service.queue.items[0]["rule_id"] == rule.id
