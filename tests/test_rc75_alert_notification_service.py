from uuid import uuid4

import pytest

from app.domains.alerts.alert_notification_service import AlertNotificationService


class FakeEvaluationService:
    def __init__(self, result):
        self.result = result

    async def evaluate_for_offer(self, *, offer_id, current_price, previous_price=None, price_change=None):
        return self.result


class FakeNotificationRepository:
    def __init__(self):
        self.items = []

    async def create(self, payload):
        item = {
            "id": str(uuid4()),
            **payload,
        }
        self.items.append(item)
        return item


@pytest.mark.asyncio
async def test_alert_notification_service_enqueues_triggered_alerts():
    offer_id = uuid4()
    repo = FakeNotificationRepository()

    service = AlertNotificationService(
        FakeEvaluationService(
            {
                "evaluated_count": 2,
                "triggered_count": 1,
                "results": [
                    {
                        "rule_id": str(uuid4()),
                        "offer_id": str(offer_id),
                        "rule_type": "TARGET_PRICE",
                        "triggered": True,
                        "reason": "target_price_reached",
                        "message": "Target price reached.",
                    },
                    {
                        "rule_id": str(uuid4()),
                        "offer_id": str(offer_id),
                        "rule_type": "DROP_PERCENT",
                        "triggered": False,
                        "reason": "price_not_down",
                        "message": "Price drop threshold not reached.",
                    },
                ],
            }
        ),
        repo,
    )

    result = await service.evaluate_and_enqueue(
        offer_id=offer_id,
        current_price=object(),
    )

    assert result["evaluated_count"] == 2
    assert result["triggered_count"] == 1
    assert result["queued_count"] == 1
    assert repo.items[0]["notification_type"] == "TARGET_PRICE"
    assert repo.items[0]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_alert_notification_service_does_not_enqueue_untriggered_alerts():
    offer_id = uuid4()
    repo = FakeNotificationRepository()

    service = AlertNotificationService(
        FakeEvaluationService(
            {
                "evaluated_count": 1,
                "triggered_count": 0,
                "results": [
                    {
                        "rule_id": str(uuid4()),
                        "offer_id": str(offer_id),
                        "rule_type": "TARGET_PRICE",
                        "triggered": False,
                        "reason": "target_price_not_reached",
                        "message": "Target price not reached.",
                    },
                ],
            }
        ),
        repo,
    )

    result = await service.evaluate_and_enqueue(
        offer_id=offer_id,
        current_price=object(),
    )

    assert result["queued_count"] == 0
    assert repo.items == []
