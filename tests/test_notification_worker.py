from uuid import uuid4

import pytest

from app.domains.notifications.senders import FailingNotificationSender, InAppNotificationSender
from app.domains.notifications.worker import NotificationWorker


class Notification:
    def __init__(self):
        self.id = uuid4()
        self.status = "PENDING"
        self.sent_at = None
        self.failed_at = None
        self.error = None


class FakeRepository:
    def __init__(self, items):
        self.items = items
        self.saved = []

    async def list_pending(self, limit=50):
        return self.items[:limit]

    async def save(self, notification):
        self.saved.append(notification)
        return notification


@pytest.mark.asyncio
async def test_notification_worker_marks_sent():
    notification = Notification()
    repo = FakeRepository([notification])

    result = await NotificationWorker(repo, InAppNotificationSender()).process_pending()

    assert result["processed_count"] == 1
    assert result["sent_count"] == 1
    assert result["failed_count"] == 0
    assert notification.status == "SENT"
    assert notification.sent_at is not None
    assert repo.saved == [notification]


@pytest.mark.asyncio
async def test_notification_worker_marks_failed():
    notification = Notification()
    repo = FakeRepository([notification])

    result = await NotificationWorker(repo, FailingNotificationSender()).process_pending()

    assert result["processed_count"] == 1
    assert result["sent_count"] == 0
    assert result["failed_count"] == 1
    assert notification.status == "FAILED"
    assert notification.failed_at is not None
    assert notification.error == "notification_send_failed"


@pytest.mark.asyncio
async def test_notification_worker_respects_limit():
    items = [Notification(), Notification(), Notification()]
    repo = FakeRepository(items)

    result = await NotificationWorker(repo, InAppNotificationSender()).process_pending(limit=2)

    assert result["processed_count"] == 2
    assert result["sent_count"] == 2
