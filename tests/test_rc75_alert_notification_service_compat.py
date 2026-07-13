from uuid import uuid4

import pytest

from app.domains.alerts.alert_notification_service import AlertNotificationService


class DummyDB:
    pass


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
async def test_explicit_dependency_injection_mode_still_works():
    offer_id = uuid4()
    repo = FakeNotificationRepository()

    service = AlertNotificationService(
        FakeEvaluationService(
            {
                "evaluated_count": 1,
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
                ],
            }
        ),
        repo,
    )

    result = await service.evaluate_and_enqueue(
        offer_id=offer_id,
        current_price=object(),
    )

    assert result["queued_count"] == 1


def test_legacy_db_constructor_does_not_import_repositories_immediately():
    service = AlertNotificationService(DummyDB())

    assert service.db is not None
    assert service.evaluation_service is None
    assert service.notification_repository is None


@pytest.mark.asyncio
async def test_legacy_db_mode_allows_dependencies_to_be_assigned_after_construction():
    offer_id = uuid4()
    repo = FakeNotificationRepository()

    service = AlertNotificationService(DummyDB())
    service.evaluation_service = FakeEvaluationService(
        {
            "evaluated_count": 1,
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
            ],
        }
    )
    service.notification_repository = repo

    result = await service.evaluate_and_queue(
        offer_id=offer_id,
        current_price=object(),
    )

    assert result["queued_count"] == 1
