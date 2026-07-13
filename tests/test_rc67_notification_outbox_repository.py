from app.domains.notifications.outbox.outbox_models import NotificationOutboxItem
from app.domains.notifications.outbox.outbox_repository import InMemoryNotificationOutboxRepository


def test_rc67_outbox_repository_add_get_count_clear():
    repo = InMemoryNotificationOutboxRepository()
    item = NotificationOutboxItem(user_id="user-1", title="Title", message="Message")

    saved = repo.add(item)

    assert repo.count() == 1
    assert repo.get(saved.id).user_id == "user-1"

    repo.clear()
    assert repo.count() == 0


def test_rc67_outbox_repository_lists_only_pending_items():
    repo = InMemoryNotificationOutboxRepository()
    pending = NotificationOutboxItem(user_id="user-1", title="Pending", message="Message")
    delivered = NotificationOutboxItem(user_id="user-1", title="Delivered", message="Message")
    delivered.mark_delivered()

    repo.add(delivered)
    repo.add(pending)

    pending_items = repo.list_pending()

    assert len(pending_items) == 1
    assert pending_items[0].title == "Pending"
