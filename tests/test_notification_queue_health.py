import pytest

from app.domains.notifications.health import NotificationQueueHealthService


class FakeRepository:
    def __init__(self, counts):
        self.counts = counts

    async def count_by_status(self, status):
        return self.counts.get(status, 0)


@pytest.mark.asyncio
async def test_notification_queue_health_passes_when_no_failed():
    result = await NotificationQueueHealthService(
        FakeRepository({"PENDING": 2, "SENT": 5, "FAILED": 0})
    ).check()

    assert result["name"] == "notification_queue"
    assert result["passed"] is True
    assert result["data"]["pending_count"] == 2
    assert result["data"]["failed_count"] == 0


@pytest.mark.asyncio
async def test_notification_queue_health_fails_when_failed_exists():
    result = await NotificationQueueHealthService(
        FakeRepository({"PENDING": 0, "SENT": 5, "FAILED": 1})
    ).check()

    assert result["passed"] is False
    assert result["error"] == "failed_notifications_exist"
