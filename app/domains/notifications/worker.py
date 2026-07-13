from datetime import datetime, timezone


class NotificationWorker:
    def __init__(self, repository, sender):
        self.repository = repository
        self.sender = sender

    async def process_pending(self, limit: int = 50):
        pending = await self.repository.list_pending(limit=limit)

        processed = []
        sent_count = 0
        failed_count = 0

        for notification in pending:
            try:
                await self.sender.send(notification)
                notification.status = "SENT"
                notification.sent_at = datetime.now(timezone.utc)
                notification.error = None

                if hasattr(self.repository, "save"):
                    await self.repository.save(notification)

                sent_count += 1
                processed.append(
                    {
                        "id": str(notification.id),
                        "status": "SENT",
                        "error": None,
                    }
                )
            except Exception as exc:
                notification.status = "FAILED"
                notification.failed_at = datetime.now(timezone.utc)
                notification.error = str(exc)

                if hasattr(self.repository, "save"):
                    await self.repository.save(notification)

                failed_count += 1
                processed.append(
                    {
                        "id": str(notification.id),
                        "status": "FAILED",
                        "error": str(exc),
                    }
                )

        return {
            "processed_count": len(processed),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "items": processed,
        }
