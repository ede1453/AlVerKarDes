from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class NotificationMessage:
    notification_id: str
    user_id: str
    channel: str
    title: str
    message: str
    payload: dict = field(default_factory=dict)
    status: str = "PENDING"
    provider: str = "mock"
    provider_response: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class NotificationDeliveryResult:
    batch_id: str
    user_id: str
    requested_channels: list[str]
    delivered_count: int
    failed_count: int
    messages: list[NotificationMessage]
    metadata: dict = field(default_factory=dict)


def create_notification_id() -> str:
    return str(uuid4())


def create_notification_batch_id() -> str:
    return str(uuid4())
