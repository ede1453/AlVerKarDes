from datetime import datetime, timezone

from app.domains.watchlist.watchlist_models import WatchlistItem


class InMemoryWatchlistRepository:
    def __init__(self):
        self._items: dict[str, WatchlistItem] = {}

    def add(self, item: WatchlistItem) -> WatchlistItem:
        self._items[item.id] = item
        return item

    def get(self, item_id: str):
        return self._items.get(item_id)

    def list_for_user(self, user_id: str):
        return [
            item for item in self._items.values()
            if item.user_id == user_id
        ]

    def update_evaluation(self, item_id: str, evaluation: dict):
        item = self._items[item_id]
        item.last_evaluation = evaluation
        item.updated_at = datetime.now(timezone.utc)
        return item

    def deactivate(self, item_id: str):
        item = self._items[item_id]
        item.status = "INACTIVE"
        item.updated_at = datetime.now(timezone.utc)
        return item

    def clear(self):
        self._items.clear()
