from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class NotificationProviderRegistry:
    SUPPORTED_CHANNELS = {"push", "email", "in_app"}

    def __init__(self) -> None:
        self._providers: dict[str, dict[str, Any]] = {}

    def register_provider(
        self,
        *,
        provider_id: str,
        channel: str,
        priority: int = 100,
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_channel = channel.lower()

        if normalized_channel not in self.SUPPORTED_CHANNELS:
            return {
                "registered": False,
                "reason": "UNSUPPORTED_CHANNEL",
                "provider": None,
            }

        provider = {
            "provider_id": provider_id,
            "channel": normalized_channel,
            "priority": int(priority),
            "enabled": bool(enabled),
            "metadata": metadata or {},
            "registered_at": now_iso(),
        }
        self._providers[provider_id] = provider

        return {
            "registered": True,
            "reason": "PROVIDER_REGISTERED",
            "provider": deepcopy(provider),
            "metadata": {
                "registry_version": "notification_provider_registry_v1"
            },
        }

    def select_provider(
        self,
        *,
        channel: str,
    ) -> dict[str, Any]:
        normalized_channel = channel.lower()

        candidates = [
            provider
            for provider in self._providers.values()
            if provider["channel"] == normalized_channel
            and provider["enabled"]
        ]

        candidates.sort(
            key=lambda item: (
                item["priority"],
                item["provider_id"],
            )
        )

        if not candidates:
            return {
                "selected": False,
                "reason": "PROVIDER_NOT_FOUND",
                "provider": None,
            }

        return {
            "selected": True,
            "reason": "PROVIDER_SELECTED",
            "provider": deepcopy(candidates[0]),
        }


class DeliveryPolicyEngine:
    def evaluate(
        self,
        *,
        notification: dict[str, Any],
        user_preferences: dict[str, Any],
        provider_available: bool,
        unsubscribe_status: bool,
    ) -> dict[str, Any]:
        reasons: list[str] = []

        if unsubscribe_status:
            reasons.append("USER_UNSUBSCRIBED")

        if not provider_available:
            reasons.append("PROVIDER_UNAVAILABLE")

        enabled_channels = {
            str(item).lower()
            for item in user_preferences.get(
                "enabled_channels",
                [],
            )
        }

        channel = str(
            notification.get("channel", "")
        ).lower()

        if channel not in enabled_channels:
            reasons.append("CHANNEL_DISABLED")

        if notification.get("status") in {
            "DELIVERED",
            "CANCELLED",
        }:
            reasons.append("NOTIFICATION_FINALIZED")

        allowed = len(reasons) == 0

        return {
            "allowed": allowed,
            "reason": (
                "DELIVERY_ALLOWED"
                if allowed
                else "DELIVERY_BLOCKED"
            ),
            "blocking_reasons": reasons,
            "metadata": {
                "policy_version": "notification_delivery_policy_v1"
            },
        }


class SubscriptionComplianceService:
    def __init__(self) -> None:
        self._subscriptions: dict[str, dict[str, Any]] = {}

    def set_subscription(
        self,
        *,
        user_id: str,
        channel: str,
        subscribed: bool,
        source: str,
    ) -> dict[str, Any]:
        key = f"{user_id}:{channel.lower()}"

        record = {
            "subscription_id": str(uuid4()),
            "user_id": user_id,
            "channel": channel.lower(),
            "subscribed": bool(subscribed),
            "source": source,
            "updated_at": now_iso(),
        }

        self._subscriptions[key] = record

        return {
            "updated": True,
            "subscription": deepcopy(record),
            "metadata": {
                "compliance_version": "notification_subscription_v1"
            },
        }

    def is_unsubscribed(
        self,
        *,
        user_id: str,
        channel: str,
    ) -> bool:
        key = f"{user_id}:{channel.lower()}"
        record = self._subscriptions.get(key)

        if record is None:
            return False

        return not record["subscribed"]


class NotificationExperimentService:
    def __init__(self) -> None:
        self._experiments: dict[str, dict[str, Any]] = {}

    def create_experiment(
        self,
        *,
        experiment_id: str,
        variants: list[str],
        enabled: bool = True,
    ) -> dict[str, Any]:
        cleaned = sorted(
            {
                str(item).strip()
                for item in variants
                if str(item).strip()
            }
        )

        if len(cleaned) < 2:
            return {
                "created": False,
                "reason": "AT_LEAST_TWO_VARIANTS_REQUIRED",
                "experiment": None,
            }

        experiment = {
            "experiment_id": experiment_id,
            "variants": cleaned,
            "enabled": enabled,
            "created_at": now_iso(),
        }
        self._experiments[experiment_id] = experiment

        return {
            "created": True,
            "experiment": deepcopy(experiment),
        }

    def assign_variant(
        self,
        *,
        experiment_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        experiment = self._experiments.get(
            experiment_id
        )

        if experiment is None:
            return {
                "assigned": False,
                "reason": "EXPERIMENT_NOT_FOUND",
            }

        if not experiment["enabled"]:
            return {
                "assigned": False,
                "reason": "EXPERIMENT_DISABLED",
            }

        variants = experiment["variants"]
        index = sum(
            ord(char)
            for char in user_id
        ) % len(variants)

        return {
            "assigned": True,
            "experiment_id": experiment_id,
            "user_id": user_id,
            "variant": variants[index],
            "metadata": {
                "experiment_version": "notification_experiment_v1"
            },
        }


class NotificationPerformanceService:
    def summarize(
        self,
        *,
        delivery_attempts: list[dict[str, Any]],
        engagement_events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        total_attempts = len(delivery_attempts)
        successful_attempts = sum(
            1
            for item in delivery_attempts
            if item.get("successful")
        )

        delivered_events = sum(
            1
            for item in engagement_events
            if str(item.get("event_type", "")).upper()
            == "DELIVERED"
        )
        opened_events = sum(
            1
            for item in engagement_events
            if str(item.get("event_type", "")).upper()
            == "OPENED"
        )
        clicked_events = sum(
            1
            for item in engagement_events
            if str(item.get("event_type", "")).upper()
            == "CLICKED"
        )
        converted_events = sum(
            1
            for item in engagement_events
            if str(item.get("event_type", "")).upper()
            == "CONVERTED"
        )

        return {
            "attempt_count": total_attempts,
            "successful_attempt_count": successful_attempts,
            "delivery_success_rate": (
                round(
                    successful_attempts / total_attempts,
                    4,
                )
                if total_attempts
                else 0.0
            ),
            "delivered_event_count": delivered_events,
            "open_rate": (
                round(
                    opened_events / delivered_events,
                    4,
                )
                if delivered_events
                else 0.0
            ),
            "click_rate": (
                round(
                    clicked_events / delivered_events,
                    4,
                )
                if delivered_events
                else 0.0
            ),
            "conversion_rate": (
                round(
                    converted_events / delivered_events,
                    4,
                )
                if delivered_events
                else 0.0
            ),
            "metadata": {
                "performance_version": "notification_performance_v1"
            },
        }


class NotificationProviderGovernanceService:
    def __init__(self) -> None:
        self.providers = NotificationProviderRegistry()
        self.delivery_policy = DeliveryPolicyEngine()
        self.compliance = SubscriptionComplianceService()
        self.experiments = NotificationExperimentService()
        self.performance = NotificationPerformanceService()
