from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

PENDING = "PENDING"
PROCESSING = "PROCESSING"
DELIVERED = "DELIVERED"
FAILED = "FAILED"
DEAD_LETTER = "DEAD_LETTER"


@dataclass
class NotificationOutboxItem:
    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    channel: str = "in_app"
    title: str = ""
    message: str = ""
    payload: dict = field(default_factory=dict)
    status: str = PENDING
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: datetime | None = None
    last_error: str | None = None
    provider: str = "mock"
    idempotency_key: str | None = None
    snoozed_until: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def snooze(self, until: str) -> None:
        self.snoozed_until = until
        self.updated_at = datetime.now(timezone.utc)

    def mark_processing(self) -> None:
        self.status = PROCESSING
        self.updated_at = datetime.now(timezone.utc)

    def mark_delivered(self) -> None:
        self.status = DELIVERED
        self.last_error = None
        self.updated_at = datetime.now(timezone.utc)

    def mark_failed(
        self,
        error: str,
        next_retry_at: datetime | None = None,
    ) -> None:
        self.retry_count += 1
        self.last_error = error

        if self.retry_count >= self.max_retries:
            self.status = DEAD_LETTER
            self.next_retry_at = None
        else:
            self.status = FAILED
            self.next_retry_at = next_retry_at

        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "channel": self.channel,
            "title": self.title,
            "message": self.message,
            "payload": self.payload,
            "status": self.status,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "last_error": self.last_error,
            "provider": self.provider,
            "idempotency_key": self.idempotency_key,
            "snoozed_until": self.snoozed_until,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def mark_pending_for_retry(self) -> None:
        self.status = PENDING
        self.updated_at = datetime.now(timezone.utc)

    def replay_from_dead_letter(
        self,
        replay_reason: str = "manual_replay",
        replayed_by: str = "system",
    ) -> None:
        existing = self.payload.get("dlq_replay", {})
        replay_count = int(existing.get("replay_count", 0)) + 1

        self.payload["dlq_replay"] = {
            "reason": replay_reason,
            "replayed_by": replayed_by,
            "replay_count": replay_count,
            "last_replayed_at": datetime.now(timezone.utc).isoformat(),
        }

        self.status = PENDING
        self.last_error = None
        self.next_retry_at = None
        self.updated_at = datetime.now(timezone.utc)