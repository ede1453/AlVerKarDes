from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


class ConnectorOperationsService:
    REQUIRED_ITEM_FIELDS = {
        "external_offer_id",
        "product_title",
        "product_url",
        "price",
        "currency",
    }

    def __init__(self) -> None:
        self._credential_profiles: dict[str, dict[str, Any]] = {}
        self._schedules: dict[str, dict[str, Any]] = {}
        self._retry_states: dict[str, dict[str, Any]] = {}
        self._metrics: dict[str, dict[str, Any]] = {}

    # RC120 — Credential reference profiles
    def register_credential_profile(
        self,
        *,
        profile_id: str,
        provider: str,
        secret_reference: str,
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not secret_reference or secret_reference.strip() == "":
            return {
                "registered": False,
                "reason": "SECRET_REFERENCE_REQUIRED",
                "profile": None,
            }

        forbidden_fragments = [
            "password=",
            "secret=",
            "token=",
            "api_key=",
        ]

        lowered = secret_reference.lower()
        if any(fragment in lowered for fragment in forbidden_fragments):
            return {
                "registered": False,
                "reason": "INLINE_SECRET_NOT_ALLOWED",
                "profile": None,
            }

        profile = {
            "profile_id": profile_id,
            "provider": provider,
            "secret_reference": secret_reference,
            "enabled": enabled,
            "metadata": metadata or {},
            "registered_at": now_iso(),
        }
        self._credential_profiles[profile_id] = profile

        return {
            "registered": True,
            "reason": "CREDENTIAL_PROFILE_REGISTERED",
            "profile": dict(profile),
            "metadata": {
                "credential_version": "connector_credentials_v1"
            },
        }

    def get_credential_profile(
        self,
        profile_id: str,
    ) -> dict[str, Any] | None:
        profile = self._credential_profiles.get(profile_id)
        return dict(profile) if profile else None

    # RC121 — Source item schema validation
    def validate_source_items(
        self,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        valid_items: list[dict[str, Any]] = []
        invalid_items: list[dict[str, Any]] = []

        for index, item in enumerate(items):
            errors: list[str] = []

            for field in sorted(self.REQUIRED_ITEM_FIELDS):
                if item.get(field) in {None, ""}:
                    errors.append(f"MISSING_{field.upper()}")

            try:
                price = float(item.get("price", 0))
            except (TypeError, ValueError):
                price = 0

            if price <= 0:
                errors.append("INVALID_PRICE")

            if errors:
                invalid_items.append(
                    {
                        "index": index,
                        "errors": sorted(set(errors)),
                        "item": item,
                    }
                )
                continue

            normalized = dict(item)
            normalized["price"] = price
            normalized["currency"] = str(
                item["currency"]
            ).upper()
            valid_items.append(normalized)

        return {
            "valid": len(invalid_items) == 0,
            "valid_count": len(valid_items),
            "invalid_count": len(invalid_items),
            "valid_items": valid_items,
            "invalid_items": invalid_items,
            "metadata": {
                "validation_version": "source_item_validation_v1"
            },
        }

    # RC122 — Retry/backoff policy
    def calculate_retry(
        self,
        *,
        operation_key: str,
        max_attempts: int = 5,
        base_delay_seconds: int = 30,
        multiplier: float = 2.0,
    ) -> dict[str, Any]:
        state = self._retry_states.get(
            operation_key,
            {
                "attempt": 0,
                "exhausted": False,
            },
        )

        if state["exhausted"]:
            return {
                "scheduled": False,
                "reason": "RETRY_EXHAUSTED",
                "operation_key": operation_key,
                **state,
            }

        next_attempt = state["attempt"] + 1

        if next_attempt > max_attempts:
            state["exhausted"] = True
            self._retry_states[operation_key] = state
            return {
                "scheduled": False,
                "reason": "RETRY_EXHAUSTED",
                "operation_key": operation_key,
                **state,
            }

        delay = int(
            base_delay_seconds
            * (multiplier ** (next_attempt - 1))
        )
        next_retry_at = (
            now_utc() + timedelta(seconds=delay)
        ).isoformat()

        state = {
            "attempt": next_attempt,
            "max_attempts": max_attempts,
            "delay_seconds": delay,
            "next_retry_at": next_retry_at,
            "exhausted": next_attempt >= max_attempts,
        }
        self._retry_states[operation_key] = state

        return {
            "scheduled": True,
            "reason": "RETRY_SCHEDULED",
            "operation_key": operation_key,
            **state,
            "metadata": {
                "retry_version": "connector_retry_backoff_v1"
            },
        }

    def reset_retry(self, operation_key: str) -> dict[str, Any]:
        self._retry_states.pop(operation_key, None)
        return {
            "reset": True,
            "operation_key": operation_key,
        }

    # RC123 — Connector schedules
    def register_schedule(
        self,
        *,
        schedule_id: str,
        source_id: str,
        interval_minutes: int,
        enabled: bool = True,
    ) -> dict[str, Any]:
        if interval_minutes <= 0:
            return {
                "registered": False,
                "reason": "INVALID_INTERVAL",
                "schedule": None,
            }

        schedule = {
            "schedule_id": schedule_id,
            "source_id": source_id,
            "interval_minutes": interval_minutes,
            "enabled": enabled,
            "last_run_at": None,
            "next_run_at": (
                now_utc()
                + timedelta(minutes=interval_minutes)
            ).isoformat(),
            "registered_at": now_iso(),
        }
        self._schedules[schedule_id] = schedule

        return {
            "registered": True,
            "reason": "SCHEDULE_REGISTERED",
            "schedule": dict(schedule),
            "metadata": {
                "schedule_version": "connector_schedule_v1"
            },
        }

    def mark_schedule_run(
        self,
        schedule_id: str,
    ) -> dict[str, Any]:
        schedule = self._schedules.get(schedule_id)

        if schedule is None:
            return {
                "updated": False,
                "reason": "SCHEDULE_NOT_FOUND",
                "schedule": None,
            }

        current = now_utc()
        schedule["last_run_at"] = current.isoformat()
        schedule["next_run_at"] = (
            current
            + timedelta(
                minutes=schedule["interval_minutes"]
            )
        ).isoformat()

        return {
            "updated": True,
            "reason": "SCHEDULE_RUN_RECORDED",
            "schedule": dict(schedule),
        }

    def list_due_schedules(
        self,
        *,
        at_time: str | None = None,
    ) -> dict[str, Any]:
        reference = (
            datetime.fromisoformat(at_time)
            if at_time
            else now_utc()
        )

        due = [
            dict(schedule)
            for schedule in self._schedules.values()
            if schedule["enabled"]
            and datetime.fromisoformat(
                schedule["next_run_at"]
            ) <= reference
        ]

        return {
            "due_count": len(due),
            "schedules": due,
            "metadata": {
                "schedule_version": "connector_schedule_v1"
            },
        }

    # RC124 — Operational metrics
    def record_run_metrics(
        self,
        *,
        source_id: str,
        collected_count: int,
        ingested_count: int,
        failed_count: int,
        duration_ms: float,
    ) -> dict[str, Any]:
        metrics = self._metrics.setdefault(
            source_id,
            {
                "source_id": source_id,
                "run_count": 0,
                "total_collected": 0,
                "total_ingested": 0,
                "total_failed": 0,
                "total_duration_ms": 0.0,
                "last_recorded_at": None,
            },
        )

        metrics["run_count"] += 1
        metrics["total_collected"] += collected_count
        metrics["total_ingested"] += ingested_count
        metrics["total_failed"] += failed_count
        metrics["total_duration_ms"] += float(duration_ms)
        metrics["last_recorded_at"] = now_iso()

        return {
            "recorded": True,
            "metrics": self.get_metrics(source_id),
        }

    def get_metrics(
        self,
        source_id: str,
    ) -> dict[str, Any]:
        metrics = self._metrics.get(source_id)

        if metrics is None:
            return {
                "source_id": source_id,
                "run_count": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "total_collected": 0,
                "total_ingested": 0,
                "total_failed": 0,
                "last_recorded_at": None,
                "metadata": {
                    "metrics_version": "connector_metrics_v1"
                },
            }

        processed = (
            metrics["total_ingested"]
            + metrics["total_failed"]
        )

        success_rate = (
            metrics["total_ingested"] / processed
            if processed > 0
            else 0.0
        )

        average_duration = (
            metrics["total_duration_ms"]
            / metrics["run_count"]
            if metrics["run_count"] > 0
            else 0.0
        )

        return {
            "source_id": source_id,
            "run_count": metrics["run_count"],
            "success_rate": round(success_rate, 4),
            "average_duration_ms": round(
                average_duration,
                3,
            ),
            "total_collected": metrics[
                "total_collected"
            ],
            "total_ingested": metrics[
                "total_ingested"
            ],
            "total_failed": metrics[
                "total_failed"
            ],
            "last_recorded_at": metrics[
                "last_recorded_at"
            ],
            "metadata": {
                "metrics_version": "connector_metrics_v1"
            },
        }
