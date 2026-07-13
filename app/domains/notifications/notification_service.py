from app.domains.events.event_bus_service import EventBusService
from app.domains.notifications.notification_models import (
    NotificationDeliveryResult,
    NotificationMessage,
    create_notification_batch_id,
    create_notification_id,
)
from app.domains.notifications.notification_policy import NotificationPolicy
from app.domains.notifications.notification_provider import (
    ExternalNotificationBoundaryProvider,
    MockNotificationProvider,
)
from app.domains.notifications.notification_serializer import serialize_delivery_result


class NotificationService:
    def __init__(
        self,
        policy: NotificationPolicy | None = None,
        mock_provider: MockNotificationProvider | None = None,
        external_provider: ExternalNotificationBoundaryProvider | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.policy = policy or NotificationPolicy()
        self.mock_provider = mock_provider or MockNotificationProvider()
        self.external_provider = external_provider or ExternalNotificationBoundaryProvider()
        self.event_bus_service = event_bus_service or EventBusService()

    def deliver(self, payload: dict):
        user_id = payload["user_id"]
        channels = payload.get("channels") or ["in_app"]
        provider_name = payload.get("provider", "mock")
        title = payload["title"]
        message = payload["message"]
        notification_payload = payload.get("payload", {})

        messages = []

        for channel in channels:
            policy_result = self.policy.evaluate(
                user_id=user_id,
                channel=channel,
                title=title,
                message=message,
            )

            if not policy_result["allowed"]:
                messages.append(
                    NotificationMessage(
                        notification_id=create_notification_id(),
                        user_id=user_id,
                        channel=channel,
                        title=title,
                        message=message,
                        payload=notification_payload,
                        status="FAILED",
                        provider=provider_name,
                        provider_response={"reason": policy_result["reason"]},
                        metadata={"warnings": policy_result["warnings"]},
                    )
                )
                continue

            provider = self.mock_provider if provider_name == "mock" else self.external_provider
            response = provider.send(
                channel=channel,
                user_id=user_id,
                title=title,
                message=message,
                payload=notification_payload,
            )

            status = "DELIVERED" if response["status"] == "DELIVERED" else response["status"]

            messages.append(
                NotificationMessage(
                    notification_id=create_notification_id(),
                    user_id=user_id,
                    channel=channel,
                    title=title,
                    message=message,
                    payload=notification_payload,
                    status=status,
                    provider=provider.name,
                    provider_response=response,
                    metadata={"warnings": policy_result["warnings"]},
                )
            )

        delivered_count = sum(1 for item in messages if item.status == "DELIVERED")
        failed_count = len(messages) - delivered_count

        result = NotificationDeliveryResult(
            batch_id=create_notification_batch_id(),
            user_id=user_id,
            requested_channels=channels,
            delivered_count=delivered_count,
            failed_count=failed_count,
            messages=messages,
            metadata={"notification_version": "notification_boundary_v1"},
        )

        serialized = serialize_delivery_result(result)

        self.event_bus_service.publish(
            {
                "event_type": "notification.delivery_completed",
                "source": "notifications",
                "payload": {
                    "batch_id": serialized["batch_id"],
                    "user_id": serialized["user_id"],
                    "delivered_count": serialized["delivered_count"],
                    "failed_count": serialized["failed_count"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def deliver_from_smart_alert(self, payload: dict):
        alert = payload["smart_alert"]
        return self.deliver(
            {
                "user_id": payload["user_id"],
                "channels": alert.get("channels") or payload.get("channels") or ["in_app"],
                "title": alert.get("title", "Shopping alert"),
                "message": alert.get("message", "A shopping alert was triggered."),
                "payload": {
                    "smart_alert": alert,
                    "source": "smart_alert",
                },
                "provider": payload.get("provider", "mock"),
            }
        )
