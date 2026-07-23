from app.domains.notifications.outbox.outbox_models import NotificationOutboxItem
from app.domains.notifications.outbox.outbox_repository import InMemoryNotificationOutboxRepository


async def test_rc67_outbox_repository_add_get_count_clear():
    repo = InMemoryNotificationOutboxRepository()
    item = NotificationOutboxItem(user_id="user-1", title="Title", message="Message")

    saved = await repo.add(item)

    assert await repo.count() == 1
    found = await repo.get(saved.id)
    assert found.user_id == "user-1"

    await repo.clear()
    assert await repo.count() == 0


async def test_rc67_outbox_repository_lists_only_pending_items():
    repo = InMemoryNotificationOutboxRepository()
    pending = NotificationOutboxItem(user_id="user-1", title="Pending", message="Message")
    delivered = NotificationOutboxItem(user_id="user-1", title="Delivered", message="Message")
    delivered.mark_delivered()

    await repo.add(delivered)
    await repo.add(pending)

    pending_items = await repo.list_pending()

    assert len(pending_items) == 1
    assert pending_items[0].title == "Pending"
