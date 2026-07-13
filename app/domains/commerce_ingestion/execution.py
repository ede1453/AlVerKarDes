from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.domains.commerce_ingestion.adapters import AdapterFactory
from app.domains.commerce_ingestion.persistence import (
    CommercePersistenceRepository,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FeedExecutionService:
    REQUIRED_FIELDS = {
        "external_offer_id",
        "product_title",
        "product_url",
        "price",
        "currency",
    }

    def __init__(
        self,
        repository: CommercePersistenceRepository | None = None,
    ) -> None:
        self.repository = repository or CommercePersistenceRepository()

    def create_job(
        self,
        *,
        source_id: str,
        adapter_type: str,
        requested_by: str,
    ) -> dict[str, Any]:
        return self.repository.create_job(
            source_id=source_id,
            adapter_type=adapter_type,
            requested_by=requested_by,
        )

    def execute_job(
        self,
        *,
        job_id: str,
        content: str,
    ) -> dict[str, Any]:
        job = self.repository.get_job(job_id)
        if job is None:
            return {
                "executed": False,
                "reason": "JOB_NOT_FOUND",
                "job": None,
            }

        self.repository.update_job(
            job_id,
            status="RUNNING",
            started_at=now_iso(),
        )

        try:
            adapter = AdapterFactory.create(job["adapter_type"])
            items = adapter.parse(content)
        except Exception as exc:
            failed = self.repository.update_job(
                job_id,
                status="FAILED",
                completed_at=now_iso(),
                error=str(exc),
            )
            return {
                "executed": False,
                "reason": "ADAPTER_EXECUTION_FAILED",
                "job": failed,
            }

        valid_items: list[dict[str, Any]] = []
        failed_count = 0

        for item in items:
            missing = sorted(
                field
                for field in self.REQUIRED_FIELDS
                if not item.get(field)
            )

            try:
                price = float(item.get("price", 0))
            except (TypeError, ValueError):
                price = 0

            if price <= 0 and "price" not in missing:
                missing.append("price")

            if missing:
                failed_count += 1
                self.repository.quarantine_item(
                    job_id=job_id,
                    source_id=job["source_id"],
                    reason="INVALID_FEED_ITEM",
                    payload={
                        "missing_or_invalid_fields": missing,
                        "item": item,
                    },
                )
                continue

            normalized_item = dict(item)
            normalized_item["price"] = price
            normalized_item["currency"] = str(
                item["currency"]
            ).upper()
            valid_items.append(normalized_item)

        completed = self.repository.update_job(
            job_id,
            status="COMPLETED",
            completed_at=now_iso(),
            collected_count=len(items),
            ingested_count=len(valid_items),
            failed_count=failed_count,
            error=None,
        )

        return {
            "executed": True,
            "reason": "JOB_COMPLETED",
            "job": completed,
            "valid_items": valid_items,
            "metadata": {
                "execution_version": "feed_execution_v1"
            },
        }

    def replay_quarantine(
        self,
        *,
        quarantine_id: str,
    ) -> dict[str, Any]:
        item = self.repository.mark_quarantine_replayed(
            quarantine_id
        )
        if item is None:
            return {
                "replayed": False,
                "reason": "QUARANTINE_ITEM_NOT_FOUND",
                "item": None,
            }
        return {
            "replayed": True,
            "reason": "QUARANTINE_ITEM_MARKED_REPLAYED",
            "item": item,
        }
