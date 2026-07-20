from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.billing.db_models import SubscriptionModel, SubscriptionTier


def _to_dict(row: SubscriptionModel) -> dict[str, Any]:
    return {
        "user_id": str(row.user_id),
        "tier": row.tier.value if isinstance(row.tier, SubscriptionTier) else row.tier,
        "provider_reference": row.provider_reference,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


class SubscriptionDBRepository:
    """Postgres-backed repository (BILL-001). Same per-request construction
    pattern as WatchlistItemDBRepository/NotificationPreferenceDBRepository
    -- no module-level singleton holding an AsyncSession."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: str) -> dict[str, Any] | None:
        try:
            key = UUID(user_id)
        except ValueError:
            return None

        row = await self.db.get(SubscriptionModel, key)
        if row is None:
            return None
        return _to_dict(row)

    async def upsert(self, *, user_id: str, tier: str, provider_reference: str | None) -> dict[str, Any]:
        key = UUID(user_id)
        row = await self.db.get(SubscriptionModel, key)

        if row is None:
            row = SubscriptionModel(user_id=key)
            self.db.add(row)

        row.tier = SubscriptionTier(tier)
        row.provider_reference = provider_reference
        row.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(row)
        return _to_dict(row)
