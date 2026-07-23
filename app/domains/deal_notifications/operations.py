from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4

from app.domains.deal_notifications.idempotency_store_factory import get_idempotency_store

# SCALE-007 Part 2: a duplicate-send window needs to outlive any single
# request but not accumulate forever -- 24h comfortably covers any
# realistic caller-defined window_key granularity (hourly/daily buckets)
# while keeping Redis memory bounded via TTL expiry.
DEFAULT_IDEMPOTENCY_TTL_SECONDS = 86400


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


class DealNotificationOperationsService:
    def __init__(self, idempotency_store=None) -> None:
        self._attempts: dict[str, list[dict[str, Any]]] = {}
        # SCALE-007 Part 2: idempotency reservations moved to an env-driven
        # store (Redis-backed in prod, in-memory fallback for tests/local)
        # -- get_idempotency_store() is the SCALE-001 factory pattern.
        self._idempotency_store = idempotency_store or get_idempotency_store()
        self._escalations: dict[str, dict[str, Any]] = {}
        self._digests: dict[str, dict[str, Any]] = {}
        self._engagement_events: list[dict[str, Any]] = []

    # RC211 — Delivery attempts
    def record_delivery_attempt(
        self,
        *,
        notification_id: str,
        channel: str,
        provider: str,
        successful: bool,
        error: str | None = None,
        latency_ms: float = 0,
    ) -> dict[str, Any]:
        attempts = self._attempts.setdefault(
            notification_id,
            [],
        )

        attempt = {
            "attempt_id": str(uuid4()),
            "notification_id": notification_id,
            "attempt_number": len(attempts) + 1,
            "channel": channel.lower(),
            "provider": provider,
            "successful": successful,
            "error": error,
            "latency_ms": float(latency_ms),
            "created_at": now_iso(),
        }

        attempts.append(attempt)

        return {
            "recorded": True,
            "attempt": deepcopy(attempt),
            "metadata": {
                "attempt_version": "deal_notification_attempt_v1"
            },
        }

    def get_delivery_attempts(
        self,
        *,
        notification_id: str,
    ) -> dict[str, Any]:
        attempts = deepcopy(
            self._attempts.get(
                notification_id,
                [],
            )
        )

        return {
            "notification_id": notification_id,
            "attempt_count": len(attempts),
            "successful_count": sum(
                1
                for item in attempts
                if item["successful"]
            ),
            "failed_count": sum(
                1
                for item in attempts
                if not item["successful"]
            ),
            "attempts": attempts,
        }

    # RC212 — Idempotency
    def reserve_idempotency_key(
        self,
        *,
        user_id: str,
        deal_id: str,
        channel: str,
        window_key: str,
        ttl_seconds: int = DEFAULT_IDEMPOTENCY_TTL_SECONDS,
    ) -> dict[str, Any]:
        raw = "|".join(
            [
                user_id,
                deal_id,
                channel.lower(),
                window_key,
            ]
        )

        key = sha256(
            raw.encode("utf-8")
        ).hexdigest()

        # SCALE-007 Part 2: candidate notification_id generated BEFORE the
        # atomic reserve attempt, so the store's SET-NX-style check-and-set
        # is a single round-trip -- no separate "check" then "write" step
        # for a second caller to race in between (the exact TOCTOU the old
        # dict.get()-then-dict[key]= sequence had, reachable even within one
        # process since this endpoint is sync and FastAPI runs it in a
        # threadpool).
        notification_id = str(uuid4())
        existing = self._idempotency_store.reserve(key, notification_id, ttl_seconds)

        if existing is not None:
            return {
                "reserved": False,
                "reason": "DUPLICATE_NOTIFICATION",
                "idempotency_key": key,
                "notification_id": existing,
            }

        return {
            "reserved": True,
            "reason": "IDEMPOTENCY_KEY_RESERVED",
            "idempotency_key": key,
            "notification_id": notification_id,
            "metadata": {
                "idempotency_version": "deal_notification_idempotency_v1"
            },
        }

    # RC213 — Escalation
    def create_escalation(
        self,
        *,
        notification_id: str,
        current_channel: str,
        fallback_channels: list[str],
        trigger_after_failures: int = 2,
    ) -> dict[str, Any]:
        history = self.get_delivery_attempts(
            notification_id=notification_id
        )

        failed_count = history["failed_count"]

        if failed_count < trigger_after_failures:
            return {
                "created": False,
                "reason": "FAILURE_THRESHOLD_NOT_REACHED",
                "escalation": None,
            }

        escalation_id = str(uuid4())
        escalation = {
            "escalation_id": escalation_id,
            "notification_id": notification_id,
            "current_channel": current_channel.lower(),
            "fallback_channels": [
                item.lower()
                for item in fallback_channels
            ],
            "status": "PENDING",
            "trigger_after_failures": trigger_after_failures,
            "observed_failures": failed_count,
            "created_at": now_iso(),
            "completed_at": None,
        }

        self._escalations[
            escalation_id
        ] = escalation

        return {
            "created": True,
            "reason": "ESCALATION_CREATED",
            "escalation": deepcopy(escalation),
            "metadata": {
                "escalation_version": "deal_notification_escalation_v1"
            },
        }

    def complete_escalation(
        self,
        *,
        escalation_id: str,
        delivered_channel: str,
    ) -> dict[str, Any]:
        escalation = self._escalations.get(
            escalation_id
        )

        if escalation is None:
            return {
                "updated": False,
                "reason": "ESCALATION_NOT_FOUND",
            }

        escalation["status"] = "COMPLETED"
        escalation["delivered_channel"] = (
            delivered_channel.lower()
        )
        escalation["completed_at"] = now_iso()

        return {
            "updated": True,
            "escalation": deepcopy(escalation),
        }

    # RC214 — Digest
    def build_digest(
        self,
        *,
        user_id: str,
        notifications: list[dict[str, Any]],
        period_start: str,
        period_end: str,
        maximum_items: int = 20,
    ) -> dict[str, Any]:
        sorted_items = sorted(
            notifications,
            key=lambda item: (
                float(
                    item.get(
                        "confidence",
                        item.get(
                            "confidence_score",
                            0,
                        ),
                    )
                ),
                float(
                    item.get(
                        "discount_pct",
                        item.get(
                            "observed_discount_pct",
                            0,
                        ),
                    )
                ),
            ),
            reverse=True,
        )

        selected = sorted_items[
            :max(maximum_items, 0)
        ]

        digest_id = str(uuid4())
        digest = {
            "digest_id": digest_id,
            "user_id": user_id,
            "period_start": period_start,
            "period_end": period_end,
            "item_count": len(selected),
            "items": deepcopy(selected),
            "summary": (
                f"{len(selected)} fırsat özete eklendi."
            ),
            "status": "READY",
            "created_at": now_iso(),
        }

        self._digests[digest_id] = digest

        return {
            "created": True,
            "digest": deepcopy(digest),
            "metadata": {
                "digest_version": "deal_notification_digest_v1"
            },
        }

    # RC215 — Engagement metrics
    def record_engagement(
        self,
        *,
        notification_id: str,
        user_id: str,
        event_type: str,
        channel: str,
        occurred_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_type = event_type.upper()

        if normalized_type not in {
            "DELIVERED",
            "OPENED",
            "CLICKED",
            "DISMISSED",
            "CONVERTED",
        }:
            return {
                "recorded": False,
                "reason": "INVALID_ENGAGEMENT_EVENT",
            }

        event = {
            "engagement_event_id": str(uuid4()),
            "notification_id": notification_id,
            "user_id": user_id,
            "event_type": normalized_type,
            "channel": channel.lower(),
            "occurred_at": occurred_at or now_iso(),
            "metadata": metadata or {},
        }

        self._engagement_events.append(event)

        return {
            "recorded": True,
            "event": deepcopy(event),
        }

    def calculate_engagement_metrics(
        self,
        *,
        user_id: str | None = None,
        channel: str | None = None,
    ) -> dict[str, Any]:
        events = list(
            self._engagement_events
        )

        if user_id is not None:
            events = [
                item
                for item in events
                if item["user_id"] == user_id
            ]

        if channel is not None:
            normalized = channel.lower()
            events = [
                item
                for item in events
                if item["channel"] == normalized
            ]

        counts = {
            "DELIVERED": 0,
            "OPENED": 0,
            "CLICKED": 0,
            "DISMISSED": 0,
            "CONVERTED": 0,
        }

        for event in events:
            counts[event["event_type"]] += 1

        delivered = counts["DELIVERED"]

        return {
            "event_count": len(events),
            "counts": counts,
            "open_rate": (
                round(
                    counts["OPENED"] / delivered,
                    4,
                )
                if delivered
                else 0.0
            ),
            "click_rate": (
                round(
                    counts["CLICKED"] / delivered,
                    4,
                )
                if delivered
                else 0.0
            ),
            "conversion_rate": (
                round(
                    counts["CONVERTED"] / delivered,
                    4,
                )
                if delivered
                else 0.0
            ),
            "metadata": {
                "engagement_version": "deal_notification_engagement_v1"
            },
        }

    def clear(self) -> dict[str, Any]:
        self._attempts = {}
        self._idempotency_store.reset()
        self._escalations = {}
        self._digests = {}
        self._engagement_events = []
        return {"cleared": True}
