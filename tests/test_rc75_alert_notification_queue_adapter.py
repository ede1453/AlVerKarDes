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


class ListOnlyQueue:
    def __init__(self):
        self.notifications = []


class AppendQueue:
    def __init__(self):
        self.items = []

    def append(self, payload):
        self.items.append(payload)


@pytest.mark.asyncio
async def test_list_attribute_queue_is_supported():
    rule = Rule()
    service = AlertNotificationService(DummyDB())
    service.queue = ListOnlyQueue()

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

    # Domain service preserves native UUID types.
    assert service.queue.notifications[0]["rule_id"] == rule.id
    assert isinstance(service.queue.notifications[0]["rule_id"], UUID)
    assert service.queue.notifications[0]["user_id"] == rule.user_id


@pytest.mark.asyncio
async def test_sync_append_queue_is_supported():
    rule = Rule()
    service = AlertNotificationService(DummyDB())
    service.queue = AppendQueue()

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
