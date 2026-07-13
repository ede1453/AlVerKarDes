class NotificationQueueHealthService:
    def __init__(self, repository):
        self.repository = repository

    async def check(self):
        pending_count = await self.repository.count_by_status("PENDING")
        failed_count = await self.repository.count_by_status("FAILED")
        sent_count = await self.repository.count_by_status("SENT")

        passed = failed_count == 0

        return {
            "name": "notification_queue",
            "passed": passed,
            "data": {
                "pending_count": pending_count,
                "failed_count": failed_count,
                "sent_count": sent_count,
            },
            "error": None if passed else "failed_notifications_exist",
        }
