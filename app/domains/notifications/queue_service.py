from uuid import UUID

from app.domains.notifications.repository import PendingNotificationRepository
from app.domains.notifications.schemas import PendingNotificationCreate


class NotificationQueueService:
    def __init__(self, db):
        self.repository = PendingNotificationRepository(db)

    async def enqueue_triggered_alert(self, *, user_id: UUID, offer_id: UUID, rule_id: UUID, message: str, channel: str = "IN_APP"):
        return await self.repository.create(
            PendingNotificationCreate(
                user_id=user_id,
                offer_id=offer_id,
                rule_id=rule_id,
                channel=channel,
                title="Price alert triggered",
                message=message,
            )
        )
