class InAppNotificationSender:
    async def send(self, notification):
        # RC5: In-app channel is considered sent once worker marks it.
        return {
            "channel": "IN_APP",
            "notification_id": str(notification.id),
            "sent": True,
        }


class FailingNotificationSender:
    async def send(self, notification):
        raise RuntimeError("notification_send_failed")
