from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.outbox.db_models import NotificationOutboxItemModel
from app.domains.notifications.outbox.outbox_models import (
    DEAD_LETTER,
    FAILED,
    PENDING,
    PROCESSING,
    NotificationOutboxItem,
)

DEFAULT_STALE_LOCK_SECONDS = 300


class InMemoryNotificationOutboxRepository:
    """Plain in-memory test double (async methods for interface parity with
    NotificationOutboxDBRepository -- same pattern as InMemoryJobRepository,
    SCALE-003). Not used by the queue endpoints anymore (SCALE-007 Part 1);
    kept for unit tests that want a repository without a real database.
    claim_next() here is NOT safe across processes (a plain dict has no
    cross-process visibility or locking) -- it exists only so
    NotificationOutboxService's default construction still has a working
    claim path for single-process tests."""

    def __init__(self):
        self._items: dict[str, NotificationOutboxItem] = {}

    async def add(self, item: NotificationOutboxItem) -> NotificationOutboxItem:
        self._items[item.id] = deepcopy(item)
        return deepcopy(item)

    async def get(self, item_id: str) -> NotificationOutboxItem | None:
        item = self._items.get(item_id)
        return deepcopy(item) if item else None

    async def list_pending(self, limit: int = 50) -> list[NotificationOutboxItem]:
        pending = [item for item in self._items.values() if item.status == PENDING]
        pending.sort(key=lambda item: item.created_at)
        return [deepcopy(item) for item in pending[:limit]]

    async def update(self, item: NotificationOutboxItem) -> NotificationOutboxItem:
        self._items[item.id] = deepcopy(item)
        return deepcopy(item)

    async def clear(self) -> None:
        self._items.clear()

    async def count(self) -> int:
        return len(self._items)

    async def list_due_retries(self, now: datetime | None = None, limit: int = 50) -> list[NotificationOutboxItem]:
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

    async def list_dead_letters(self, limit: int = 50) -> list[NotificationOutboxItem]:
        dead_letters = [
            item for item in self._items.values()
            if item.status == DEAD_LETTER
        ]
        dead_letters.sort(key=lambda item: item.updated_at, reverse=True)
        return [deepcopy(item) for item in dead_letters[:limit]]

    async def list_all(self) -> list[NotificationOutboxItem]:
        return [deepcopy(item) for item in self._items.values()]

    async def claim_next(
        self, *, worker_id: str, stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS
    ) -> NotificationOutboxItem | None:
        stale_cutoff = datetime.now(timezone.utc) - timedelta(seconds=stale_lock_seconds)
        candidates = sorted(self._items.values(), key=lambda item: item.created_at)

        for item in candidates:
            is_stale_processing = item.status == PROCESSING and item.updated_at < stale_cutoff
            if item.status == PENDING or is_stale_processing:
                item.status = PROCESSING
                item.locked_by = worker_id
                item.locked_at = datetime.now(timezone.utc)
                item.updated_at = item.locked_at
                return deepcopy(item)

        return None


def _to_item(row: NotificationOutboxItemModel) -> NotificationOutboxItem:
    return NotificationOutboxItem(
        id=str(row.id),
        user_id=row.user_id,
        channel=row.channel,
        title=row.title,
        message=row.message,
        payload=dict(row.payload or {}),
        status=row.status,
        retry_count=row.retry_count,
        max_retries=row.max_retries,
        next_retry_at=row.next_retry_at,
        last_error=row.last_error,
        provider=row.provider,
        idempotency_key=row.idempotency_key,
        snoozed_until=row.snoozed_until,
        created_at=row.created_at,
        updated_at=row.updated_at,
        locked_by=row.locked_by,
        locked_at=row.locked_at,
    )


class NotificationOutboxDBRepository:
    """Postgres-backed repository (SCALE-007 Part 1).

    Before this, NotificationOutboxService only ever wrote to an in-memory
    dict (InMemoryNotificationOutboxRepository) -- worker-process-local,
    invisible to other workers, and lost on restart. Worse: the pre-existing
    claim_next() had NO claim mechanism at all (list_pending(limit=1) then
    mark_processing() then update() -- a read-then-write race even within a
    single process, and trivially double-claimable across processes since
    each process never saw the other's in-memory dict in the first place).

    This repository persists to the real notification_outbox_items table
    (migration 0024). claim_next() uses SELECT ... FOR UPDATE SKIP LOCKED
    (same pattern as JobDBRepository/ProviderSchedulerDBRepository, SCALE-
    003/004), so two concurrent workers racing for the same row never both
    claim it -- and never both send the same notification twice."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, item: NotificationOutboxItem) -> NotificationOutboxItem:
        row = NotificationOutboxItemModel(
            id=UUID(item.id),
            user_id=item.user_id,
            channel=item.channel,
            title=item.title,
            message=item.message,
            payload=dict(item.payload),
            status=item.status,
            retry_count=item.retry_count,
            max_retries=item.max_retries,
            next_retry_at=item.next_retry_at,
            last_error=item.last_error,
            provider=item.provider,
            idempotency_key=item.idempotency_key,
            snoozed_until=item.snoozed_until,
            created_at=item.created_at,
            updated_at=item.updated_at,
            locked_by=item.locked_by,
            locked_at=item.locked_at,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return _to_item(row)

    async def get(self, item_id: str) -> NotificationOutboxItem | None:
        try:
            key = UUID(item_id)
        except ValueError:
            return None

        row = await self.db.get(NotificationOutboxItemModel, key)
        if row is None:
            return None
        return _to_item(row)

    async def list_pending(self, limit: int = 50) -> list[NotificationOutboxItem]:
        result = await self.db.execute(
            select(NotificationOutboxItemModel)
            .where(NotificationOutboxItemModel.status == PENDING)
            .order_by(NotificationOutboxItemModel.created_at)
            .limit(limit)
        )
        return [_to_item(row) for row in result.scalars().all()]

    async def update(self, item: NotificationOutboxItem) -> NotificationOutboxItem:
        row = await self.db.get(NotificationOutboxItemModel, UUID(item.id))
        if row is None:
            return item

        row.status = item.status
        row.retry_count = item.retry_count
        row.max_retries = item.max_retries
        row.next_retry_at = item.next_retry_at
        row.last_error = item.last_error
        row.payload = dict(item.payload)
        row.snoozed_until = item.snoozed_until
        row.updated_at = item.updated_at
        # The dataclass's mark_delivered()/mark_failed()/mark_pending_for_retry()/
        # replay_from_dead_letter() (outbox_models.py) already clear
        # locked_by/locked_at when leaving PROCESSING -- update() is never
        # called for the PENDING->PROCESSING transition itself (claim_next()
        # handles that atomically at the repository layer), so trusting the
        # item's own lock fields here is correct.
        row.locked_by = item.locked_by
        row.locked_at = item.locked_at

        await self.db.commit()
        await self.db.refresh(row)
        return _to_item(row)

    async def clear(self) -> None:
        result = await self.db.execute(select(NotificationOutboxItemModel))
        for row in result.scalars().all():
            await self.db.delete(row)
        await self.db.commit()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(NotificationOutboxItemModel))
        return result.scalar_one()

    async def list_due_retries(self, now: datetime | None = None, limit: int = 50) -> list[NotificationOutboxItem]:
        now = now or datetime.now(timezone.utc)

        result = await self.db.execute(
            select(NotificationOutboxItemModel)
            .where(
                NotificationOutboxItemModel.status == FAILED,
                NotificationOutboxItemModel.next_retry_at.is_not(None),
                NotificationOutboxItemModel.next_retry_at <= now,
            )
            .order_by(NotificationOutboxItemModel.next_retry_at)
            .limit(limit)
        )
        return [_to_item(row) for row in result.scalars().all()]

    async def list_dead_letters(self, limit: int = 50) -> list[NotificationOutboxItem]:
        result = await self.db.execute(
            select(NotificationOutboxItemModel)
            .where(NotificationOutboxItemModel.status == DEAD_LETTER)
            .order_by(NotificationOutboxItemModel.updated_at.desc())
            .limit(limit)
        )
        return [_to_item(row) for row in result.scalars().all()]

    async def list_all(self) -> list[NotificationOutboxItem]:
        result = await self.db.execute(select(NotificationOutboxItemModel))
        return [_to_item(row) for row in result.scalars().all()]

    async def claim_next(
        self, *, worker_id: str, stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS
    ) -> NotificationOutboxItem | None:
        stale_cutoff = datetime.now(timezone.utc) - timedelta(seconds=stale_lock_seconds)

        stmt = (
            select(NotificationOutboxItemModel)
            .where(
                or_(
                    NotificationOutboxItemModel.status == PENDING,
                    and_(
                        NotificationOutboxItemModel.status == PROCESSING,
                        NotificationOutboxItemModel.locked_at < stale_cutoff,
                    ),
                )
            )
            .order_by(NotificationOutboxItemModel.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(stmt)
        row = result.scalars().first()

        if row is None:
            await self.db.commit()
            return None

        row.status = PROCESSING
        row.locked_by = worker_id
        row.locked_at = datetime.now(timezone.utc)
        row.updated_at = row.locked_at
        await self.db.commit()
        await self.db.refresh(row)
        return _to_item(row)
