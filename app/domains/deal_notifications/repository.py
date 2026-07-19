from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.deal_notifications.db_models import NotificationPreferenceModel


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InMemoryNotificationPreferenceRepository:
    """Plain in-memory test double (async methods for interface parity
    with NotificationPreferenceDBRepository) -- not used by the API
    anymore (CLIENT-002g); kept for unit tests that want a repository
    without a real database, same pattern as
    watchlist_repository.py::InMemoryWatchlistRepository /
    decision_memory_repository.py::InMemoryDecisionMemoryRepository."""

    def __init__(self) -> None:
        self._preferences: dict[str, dict[str, Any]] = {}

    async def get(self, user_id: str) -> dict[str, Any] | None:
        existing = self._preferences.get(user_id)
        return deepcopy(existing) if existing else None

    async def upsert(self, preferences: dict[str, Any]) -> dict[str, Any]:
        self._preferences[preferences["user_id"]] = deepcopy(preferences)
        return deepcopy(preferences)


def _to_dict(row: NotificationPreferenceModel) -> dict[str, Any]:
    return {
        "user_id": str(row.user_id),
        "enabled_channels": list(row.enabled_channels or []),
        "minimum_confidence": row.minimum_confidence,
        "minimum_discount_pct": row.minimum_discount_pct,
        "quiet_hours_enabled": row.quiet_hours_enabled,
        "quiet_hours_start": row.quiet_hours_start,
        "quiet_hours_end": row.quiet_hours_end,
        "updated_at": row.updated_at.isoformat(),
    }


class NotificationPreferenceDBRepository:
    """Postgres-backed repository (CLIENT-002g). Same shape/pattern as
    WatchlistItemDBRepository (CLIENT-002e): returns the same plain dict
    shape the in-memory repository returns, so NotificationPreferenceService
    doesn't need to change beyond adding await."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: str) -> dict[str, Any] | None:
        try:
            key = UUID(user_id)
        except ValueError:
            return None

        row = await self.db.get(NotificationPreferenceModel, key)
        if row is None:
            return None
        return _to_dict(row)

    async def upsert(self, preferences: dict[str, Any]) -> dict[str, Any]:
        key = UUID(preferences["user_id"])
        row = await self.db.get(NotificationPreferenceModel, key)

        if row is None:
            row = NotificationPreferenceModel(user_id=key)
            self.db.add(row)

        row.enabled_channels = list(preferences["enabled_channels"])
        row.minimum_confidence = preferences["minimum_confidence"]
        row.minimum_discount_pct = preferences["minimum_discount_pct"]
        row.quiet_hours_enabled = preferences["quiet_hours_enabled"]
        row.quiet_hours_start = preferences["quiet_hours_start"]
        row.quiet_hours_end = preferences["quiet_hours_end"]
        row.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(row)
        return _to_dict(row)
