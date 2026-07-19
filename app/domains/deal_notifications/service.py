from __future__ import annotations

from copy import deepcopy
from datetime import datetime, time, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DealAlertEligibilityEngine:
    def evaluate(
        self,
        *,
        deal: dict[str, Any],
        minimum_confidence: float = 70,
        minimum_discount_pct: float = 10,
        require_fresh: bool = True,
    ) -> dict[str, Any]:
        confidence = float(
            deal.get(
                "confidence_score",
                deal.get("confidence", 0),
            )
        )
        discount = float(
            deal.get(
                "observed_discount_pct",
                0,
            )
        )
        freshness = str(
            deal.get(
                "freshness_status",
                "STALE",
            )
        ).upper()

        reasons: list[str] = []

        if confidence < minimum_confidence:
            reasons.append("CONFIDENCE_TOO_LOW")

        if discount < minimum_discount_pct:
            reasons.append("DISCOUNT_TOO_LOW")

        if require_fresh and freshness != "FRESH":
            reasons.append("PRICE_NOT_FRESH")

        if deal.get("anomaly_detected", False):
            reasons.append("PRICE_ANOMALY_DETECTED")

        if deal.get("decision") not in {None, "BUY"}:
            reasons.append("DECISION_NOT_BUY")

        eligible = len(reasons) == 0

        return {
            "eligible": eligible,
            "reasons": reasons,
            "confidence": confidence,
            "discount_pct": discount,
            "freshness_status": freshness,
            "metadata": {
                "eligibility_version": "deal_alert_eligibility_v1"
            },
        }


class NotificationPreferenceService:
    def __init__(self) -> None:
        self._preferences: dict[str, dict[str, Any]] = {}

    def set_preferences(
        self,
        *,
        user_id: str,
        enabled_channels: list[str],
        minimum_confidence: float = 70,
        minimum_discount_pct: float = 10,
        quiet_hours_enabled: bool = False,
        quiet_hours_start: str = "22:00",
        quiet_hours_end: str = "08:00",
    ) -> dict[str, Any]:
        preferences = {
            "user_id": user_id,
            "enabled_channels": sorted(
                {
                    channel.lower()
                    for channel in enabled_channels
                }
            ),
            "minimum_confidence": float(
                minimum_confidence
            ),
            "minimum_discount_pct": float(
                minimum_discount_pct
            ),
            "quiet_hours_enabled": quiet_hours_enabled,
            "quiet_hours_start": quiet_hours_start,
            "quiet_hours_end": quiet_hours_end,
            "updated_at": now_iso(),
        }
        self._preferences[user_id] = preferences

        return {
            "updated": True,
            "preferences": deepcopy(preferences),
        }

    def get_preferences(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        existing = self._preferences.get(user_id)

        if existing:
            return deepcopy(existing)

        return {
            "user_id": user_id,
            "enabled_channels": ["in_app"],
            "minimum_confidence": 70.0,
            "minimum_discount_pct": 10.0,
            "quiet_hours_enabled": False,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
        }


class QuietHoursService:
    def is_quiet_time(
        self,
        *,
        at_time: str,
        start_time: str,
        end_time: str,
    ) -> dict[str, Any]:
        current = datetime.fromisoformat(
            at_time
        ).timetz().replace(tzinfo=None)

        start = time.fromisoformat(start_time)
        end = time.fromisoformat(end_time)

        if start == end:
            quiet = True
        elif start < end:
            quiet = start <= current < end
        else:
            quiet = (
                current >= start
                or current < end
            )

        return {
            "quiet": quiet,
            "current_time": current.isoformat(),
            "start_time": start_time,
            "end_time": end_time,
            "metadata": {
                "quiet_hours_version": "deal_quiet_hours_v1"
            },
        }


class NotificationChannelRouter:
    SUPPORTED_CHANNELS = {
        "in_app",
        "email",
        "push",
    }

    def route(
        self,
        *,
        enabled_channels: list[str],
        quiet: bool,
        urgent: bool,
    ) -> dict[str, Any]:
        valid = [
            channel.lower()
            for channel in enabled_channels
            if channel.lower()
            in self.SUPPORTED_CHANNELS
        ]

        deferred: list[str] = []
        immediate: list[str] = []

        for channel in valid:
            if quiet and not urgent:
                deferred.append(channel)
            else:
                immediate.append(channel)

        return {
            "immediate_channels": immediate,
            "deferred_channels": deferred,
            "dropped_channels": [
                channel
                for channel in enabled_channels
                if channel.lower()
                not in self.SUPPORTED_CHANNELS
            ],
            "metadata": {
                "router_version": "deal_notification_router_v1"
            },
        }


class DealNotificationService:
    def __init__(self) -> None:
        self.eligibility = DealAlertEligibilityEngine()
        self.preferences = NotificationPreferenceService()
        self.quiet_hours = QuietHoursService()
        self.channel_router = NotificationChannelRouter()
        self._notifications: dict[str, dict[str, Any]] = {}

    def build_notification(
        self,
        *,
        user_id: str,
        deal: dict[str, Any],
        at_time: str,
    ) -> dict[str, Any]:
        preferences = self.preferences.get_preferences(
            user_id
        )

        eligibility = self.eligibility.evaluate(
            deal=deal,
            minimum_confidence=preferences[
                "minimum_confidence"
            ],
            minimum_discount_pct=preferences[
                "minimum_discount_pct"
            ],
        )

        if not eligibility["eligible"]:
            return {
                "created": False,
                "reason": "DEAL_NOT_ELIGIBLE",
                "eligibility": eligibility,
                "notification": None,
            }

        quiet_result = {
            "quiet": False
        }

        if preferences["quiet_hours_enabled"]:
            quiet_result = (
                self.quiet_hours.is_quiet_time(
                    at_time=at_time,
                    start_time=preferences[
                        "quiet_hours_start"
                    ],
                    end_time=preferences[
                        "quiet_hours_end"
                    ],
                )
            )

        urgent = (
            eligibility["confidence"] >= 90
            and eligibility["discount_pct"] >= 30
        )

        routing = self.channel_router.route(
            enabled_channels=preferences[
                "enabled_channels"
            ],
            quiet=quiet_result["quiet"],
            urgent=urgent,
        )

        notification_id = str(uuid4())
        status = (
            "READY"
            if routing["immediate_channels"]
            else "DEFERRED"
        )

        notification = {
            "notification_id": notification_id,
            "user_id": user_id,
            "deal_id": deal.get("deal_id"),
            "product_key": deal.get(
                "canonical_product_key"
            ),
            "status": status,
            "urgent": urgent,
            "title": (
                "Çok güçlü fırsat"
                if urgent
                else "Yeni fiyat fırsatı"
            ),
            "message": (
                f"%{round(eligibility['discount_pct'], 2)} "
                "doğrulanmış indirim tespit edildi."
            ),
            "immediate_channels": routing[
                "immediate_channels"
            ],
            "deferred_channels": routing[
                "deferred_channels"
            ],
            "payload": {
                "confidence": eligibility[
                    "confidence"
                ],
                "discount_pct": eligibility[
                    "discount_pct"
                ],
                "effective_price": deal.get(
                    "effective_price",
                    deal.get("price"),
                ),
                "source_id": deal.get("source_id"),
            },
            "created_at": now_iso(),
            "delivered_at": None,
        }

        self._notifications[
            notification_id
        ] = notification

        return {
            "created": True,
            "reason": "NOTIFICATION_CREATED",
            "eligibility": eligibility,
            "routing": routing,
            "notification": deepcopy(notification),
            "metadata": {
                "service_version": "deal_notification_service_v1"
            },
        }

    def get_notification(
        self,
        notification_id: str,
    ) -> dict[str, Any] | None:
        return self._notifications.get(notification_id)

    def mark_delivered(
        self,
        *,
        notification_id: str,
        channel: str,
    ) -> dict[str, Any]:
        notification = self._notifications.get(
            notification_id
        )

        if notification is None:
            return {
                "updated": False,
                "reason": "NOTIFICATION_NOT_FOUND",
            }

        normalized_channel = channel.lower()

        if normalized_channel not in (
            notification["immediate_channels"]
            + notification["deferred_channels"]
        ):
            return {
                "updated": False,
                "reason": "CHANNEL_NOT_ROUTED",
            }

        notification["status"] = "DELIVERED"
        notification["delivered_channel"] = (
            normalized_channel
        )
        notification["delivered_at"] = now_iso()

        return {
            "updated": True,
            "notification": deepcopy(notification),
        }

    def list_notifications(
        self,
        *,
        user_id: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        items = list(
            self._notifications.values()
        )

        if user_id is not None:
            items = [
                item
                for item in items
                if item["user_id"] == user_id
            ]

        if status is not None:
            normalized = status.upper()
            items = [
                item
                for item in items
                if item["status"] == normalized
            ]

        return {
            "notification_count": len(items),
            "notifications": deepcopy(items),
        }

    def clear(self) -> dict[str, Any]:
        self._notifications.clear()
        self.preferences = (
            NotificationPreferenceService()
        )
        return {"cleared": True}
