from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from app.domains.notifications.outbox.outbox_models import DEAD_LETTER, FAILED, PENDING, NotificationOutboxItem


class InMemoryNotificationOutboxRepository:
    def __init__(self):
        self._items: dict[str, NotificationOutboxItem] = {}

    def add(self, item: NotificationOutboxItem) -> NotificationOutboxItem:
        self._items[item.id] = deepcopy(item)
        return deepcopy(item)

    def get(self, item_id: str) -> NotificationOutboxItem | None:
        item = self._items.get(item_id)
        return deepcopy(item) if item else None

    def list_pending(self, limit: int = 50) -> list[NotificationOutboxItem]:
        pending = [item for item in self._items.values() if item.status == PENDING]
        pending.sort(key=lambda item: item.created_at)
        return [deepcopy(item) for item in pending[:limit]]

    def update(self, item: NotificationOutboxItem) -> NotificationOutboxItem:
        self._items[item.id] = deepcopy(item)
        return deepcopy(item)

    def clear(self) -> None:
        self._items.clear()

    def count(self) -> int:
        return len(self._items)

    def list_due_retries(self, now: datetime | None = None, limit: int = 50) -> list[NotificationOutboxItem]:
        now = now or datetime.now(timezone.utc)

        due_items = [
            item
            for item in self._items.values()
            if item.status == FAILED
            and item.next_retry_at is not None
            and item.next_retry_at <= now
        ]

        due_items.sort(key=lambda item: item.next_retry_at)
        return [deepcopy(item) for item in due_items[:limit]]

    def list_dead_letters(self, limit: int = 50) -> list[NotificationOutboxItem]:
        dead_letters = [
            item for item in self._items.values()
            if item.status == DEAD_LETTER
        ]
        dead_letters.sort(key=lambda item: item.updated_at, reverse=True)
        return [deepcopy(item) for item in dead_letters[:limit]]

    def list_all(self) -> list[NotificationOutboxItem]:
        return [deepcopy(item) for item in self._items.values()]
