from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.models import PendingNotification
from app.domains.notifications.schemas import PendingNotificationCreate


class PendingNotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: PendingNotificationCreate):
        notification = PendingNotification(**payload.model_dump(), status="PENDING")
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def list_pending(self, limit: int = 50):
        result = await self.db.execute(
            select(PendingNotification)
            .where(PendingNotification.status == "PENDING")
            .order_by(PendingNotification.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def save(self, notification):
        await self.db.commit()
        await self.db.refresh(notification)
        return notification
        
    async def mark_sent(self, notification):
        notification.status = "SENT"
        notification.sent_at = datetime.now(timezone.utc)
        notification.error = None
        return await self.save(notification)

    async def mark_failed(self, notification, error: str):
        notification.status = "FAILED"
        notification.failed_at = datetime.now(timezone.utc)
        notification.error = error
        return await self.save(notification)
    
    async def count_by_status(self, status: str):
        result = await self.db.execute(
            select(func.count())
            .select_from(PendingNotification)
            .where(PendingNotification.status == status)
        )
        return int(result.scalar_one())