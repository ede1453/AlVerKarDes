from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.domains.commerce_ingestion.idempotency import (
    IngestionIdempotencyService,
)
from app.domains.commerce_ingestion.price_bridge import (
    PriceHistoryBridge,
)
from app.domains.commerce_ingestion.source_adapters import (
    SourceAdapterError,
    SourceAdapterFactory,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConnectorRuntimeService:
    REQUIRED_FIELDS = {
        "external_offer_id",
        "product_title",
        "product_url",
        "price",
        "currency",
    }

    def __init__(self) -> None:
        self.idempotency = IngestionIdempotencyService()
        self.price_bridge = PriceHistoryBridge()
        self._runs: dict[str, dict[str, Any]] = {}
        self._events: list[dict[str, Any]] = []

    def _event(
        self,
        *,
        event_type: str,
        run_id: str,
        source_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self._events.append(
            {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "run_id": run_id,
                "source_id": source_id,
                "details": details or {},
                "created_at": now_iso(),
            }
        )

    def execute_connector(
        self,
        *,
        source_id: str,
        adapter_type: str,
        source_config: dict[str, Any],
        canonical_product_key_field: str = "canonical_product_key",
    ) -> dict[str, Any]:
        run_id = str(uuid4())
        run = {
            "run_id": run_id,
            "source_id": source_id,
            "adapter_type": adapter_type,
            "status": "RUNNING",
            "started_at": now_iso(),
            "completed_at": None,
            "collected_count": 0,
            "ingested_count": 0,
            "duplicate_count": 0,
            "failed_count": 0,
            "errors": [],
        }
        self._runs[run_id] = run
        self._event(
            event_type="CONNECTOR_RUNTIME_STARTED",
            run_id=run_id,
            source_id=source_id,
        )

        try:
            adapter = SourceAdapterFactory.create(adapter_type)
            items = adapter.collect(source_config)
        except SourceAdapterError as exc:
            run["status"] = "FAILED"
            run["completed_at"] = now_iso()
            run["errors"].append(str(exc))
            self._event(
                event_type="CONNECTOR_RUNTIME_FAILED",
                run_id=run_id,
                source_id=source_id,
                details={"error": str(exc)},
            )
            return {
                "executed": False,
                "reason": "SOURCE_ADAPTER_FAILED",
                "run": run,
                "price_updates": [],
            }

        run["collected_count"] = len(items)
        price_updates = []

        for item in items:
            missing = [
                field
                for field in self.REQUIRED_FIELDS
                if not item.get(field)
            ]
            if missing:
                run["failed_count"] += 1
                run["errors"].append(
                    f"MISSING_FIELDS:{','.join(sorted(missing))}"
                )
                continue

            try:
                price = float(item["price"])
            except (TypeError, ValueError):
                run["failed_count"] += 1
                run["errors"].append("INVALID_PRICE")
                continue

            if price <= 0:
                run["failed_count"] += 1
                run["errors"].append("INVALID_PRICE")
                continue

            observed_at = item.get("observed_at") or now_iso()
            canonical_product_key = (
                item.get(canonical_product_key_field)
                or item["product_title"]
                .strip()
                .lower()
                .replace(" ", "-")
            )

            key = self.idempotency.build_key(
                source_id=source_id,
                external_offer_id=str(
                    item["external_offer_id"]
                ),
                observed_at=observed_at,
                price=price,
                currency=str(item["currency"]),
            )
            reservation = self.idempotency.reserve(key)

            if not reservation["reserved"]:
                run["duplicate_count"] += 1
                continue

            snapshot_id = str(uuid4())
            update = self.price_bridge.append_snapshot(
                canonical_product_key=canonical_product_key,
                source_id=source_id,
                external_offer_id=str(
                    item["external_offer_id"]
                ),
                price=price,
                currency=str(item["currency"]),
                observed_at=observed_at,
                snapshot_id=snapshot_id,
            )
            price_updates.append(update)
            run["ingested_count"] += 1

        run["status"] = (
            "COMPLETED_WITH_ERRORS"
            if run["failed_count"] > 0
            else "COMPLETED"
        )
        run["completed_at"] = now_iso()

        self._event(
            event_type="CONNECTOR_RUNTIME_COMPLETED",
            run_id=run_id,
            source_id=source_id,
            details={
                "collected_count": run["collected_count"],
                "ingested_count": run["ingested_count"],
                "duplicate_count": run["duplicate_count"],
                "failed_count": run["failed_count"],
            },
        )

        return {
            "executed": True,
            "reason": "CONNECTOR_RUNTIME_COMPLETED",
            "run": run,
            "price_updates": price_updates,
            "metadata": {
                "runtime_version": "connector_runtime_v1"
            },
        }

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self._runs.get(run_id)

    def list_events(
        self,
        *,
        source_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        events = list(self._events)

        if source_id is not None:
            events = [
                event
                for event in events
                if event["source_id"] == source_id
            ]

        if run_id is not None:
            events = [
                event
                for event in events
                if event["run_id"] == run_id
            ]

        return {
            "event_count": len(events),
            "events": events,
            "metadata": {
                "runtime_version": "connector_runtime_v1"
            },
        }
