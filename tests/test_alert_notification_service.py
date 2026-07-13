from uuid import uuid4

import pytest

from app.domains.alerts.alert_notification_service import AlertNotificationService


class Rule:
    def __init__(self):
        self.id = uuid4()
        self.user_id = uuid4()
        self.offer_id = uuid4()


class FakeQueue:
    def __init__(self):
        self.items = []

    async def enqueue_triggered_alert(self, *, user_id, offer_id, rule_id, message, channel="IN_APP"):
        item = {
            "user_id": user_id,
            "offer_id": offer_id,
            "rule_id": rule_id,
            "message": message,
            "channel": channel,
        }
        self.items.append(item)
        return item


class DummyDB:
    pass


@pytest.mark.asyncio
async def test_alert_notification_service_queues_triggered_alerts(monkeypatch):
    rule = Rule()

    service = AlertNotificationService(DummyDB())
    fake_queue = FakeQueue()
    service.queue = fake_queue

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
    assert len(fake_queue.items) == 1
    assert fake_queue.items[0]["rule_id"] == rule.id


@pytest.mark.asyncio
async def test_alert_notification_service_skips_missing_rule():
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
