from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.watchlist.db_models import WatchlistItemModel, WatchlistItemStatus
from app.domains.watchlist.watchlist_models import WatchlistItem


class InMemoryWatchlistRepository:
    """Plain in-memory test double (async methods for interface parity with
    WatchlistItemDBRepository -- see that class's docstring). Not used by
    the API anymore (CLIENT-002e); kept for unit tests that want a
    repository without a real database, same pattern as
    decision_memory_repository.py::InMemoryDecisionMemoryRepository."""

    def __init__(self):
        self._items: dict[str, WatchlistItem] = {}

    async def add(self, item: WatchlistItem) -> WatchlistItem:
        self._items[item.id] = item
        return item

    async def get(self, item_id: str):
        return self._items.get(item_id)

    async def list_for_user(self, user_id: str):
        return [
            item for item in self._items.values()
            if item.user_id == user_id
        ]

    async def update_evaluation(self, item_id: str, evaluation: dict):
        item = self._items[item_id]
        item.last_evaluation = evaluation
        item.updated_at = datetime.now(timezone.utc)
        return item

    async def deactivate(self, item_id: str):
        item = self._items[item_id]
        item.status = "INACTIVE"
        item.updated_at = datetime.now(timezone.utc)
        return item

    async def clear(self):
        self._items.clear()


def _to_item(row: WatchlistItemModel) -> WatchlistItem:
    return WatchlistItem(
        id=str(row.id),
        user_id=str(row.user_id),
        product_key=row.product_key,
        query=row.query,
        target_price=row.target_price,
        marketplaces=list(row.marketplaces or []),
        channels=list(row.channels or []),
        status=row.status.value if isinstance(row.status, WatchlistItemStatus) else row.status,
        last_evaluation=row.last_evaluation,
        metadata=dict(row.metadata_json or {}),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class WatchlistItemDBRepository:
    """Postgres-backed repository (CLIENT-002e).

    Before this, WatchlistService only ever wrote to an in-memory dict
    (InMemoryWatchlistRepository) -- functionally correct (real ownership
    checks, real per-user isolation) but not durable: a container restart
    lost every watchlist item. This repository persists to the real
    watchlist_items table (migration 0018_watchlist_items). Returns the
    same WatchlistItem dataclass the in-memory repository returns, so
    WatchlistService and watchlist_serializer need no changes -- same
    pattern as DecisionMemoryRepository (AUTH-006 Part 2)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, item: WatchlistItem) -> WatchlistItem:
        row = WatchlistItemModel(
            id=UUID(item.id),
            user_id=UUID(item.user_id),
            product_key=item.product_key,
            query=item.query,
            target_price=item.target_price,
            marketplaces=list(item.marketplaces),
            channels=list(item.channels),
            status=WatchlistItemStatus(item.status),
            last_evaluation=item.last_evaluation,
            metadata_json=dict(item.metadata),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return _to_item(row)

    async def get(self, item_id: str) -> WatchlistItem | None:
        try:
            key = UUID(item_id)
        except ValueError:
            return None

        row = await self.db.get(WatchlistItemModel, key)
        if row is None:
            return None
        return _to_item(row)

    async def list_for_user(self, user_id: str) -> list[WatchlistItem]:
        try:
            key = UUID(user_id)
        except ValueError:
            return []

        result = await self.db.execute(
            select(WatchlistItemModel).where(WatchlistItemModel.user_id == key)
        )
        return [_to_item(row) for row in result.scalars().all()]

    async def update_evaluation(self, item_id: str, evaluation: dict) -> WatchlistItem | None:
        row = await self.db.get(WatchlistItemModel, UUID(item_id))
        if row is None:
            return None

        row.last_evaluation = evaluation
        row.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(row)
        return _to_item(row)

    async def deactivate(self, item_id: str) -> WatchlistItem | None:
        row = await self.db.get(WatchlistItemModel, UUID(item_id))
        if row is None:
            return None

        row.status = WatchlistItemStatus.INACTIVE
        row.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(row)
        return _to_item(row)

    async def clear(self):
        result = await self.db.execute(select(WatchlistItemModel))
        for row in result.scalars().all():
            await self.db.delete(row)
        await self.db.commit()
