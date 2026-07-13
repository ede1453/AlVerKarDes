from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CommercePersistenceRepository:
    def __init__(self) -> None:
        self._sources: dict[str, dict[str, Any]] = {}
        self._jobs: dict[str, dict[str, Any]] = {}
        self._quarantine: dict[str, dict[str, Any]] = {}

    def save_source(self, source: dict[str, Any]) -> dict[str, Any]:
        self._sources[source["source_id"]] = deepcopy(source)
        return deepcopy(source)

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        source = self._sources.get(source_id)
        return deepcopy(source) if source else None

    def list_sources(self) -> list[dict[str, Any]]:
        return deepcopy(list(self._sources.values()))

    def create_job(
        self,
        *,
        source_id: str,
        adapter_type: str,
        requested_by: str,
    ) -> dict[str, Any]:
        job_id = str(uuid4())
        job = {
            "job_id": job_id,
            "source_id": source_id,
            "adapter_type": adapter_type,
            "requested_by": requested_by,
            "status": "PENDING",
            "created_at": now_iso(),
            "started_at": None,
            "completed_at": None,
            "collected_count": 0,
            "ingested_count": 0,
            "failed_count": 0,
            "error": None,
        }
        self._jobs[job_id] = job
        return deepcopy(job)

    def update_job(
        self,
        job_id: str,
        **changes: Any,
    ) -> dict[str, Any] | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        job.update(changes)
        return deepcopy(job)

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        job = self._jobs.get(job_id)
        return deepcopy(job) if job else None

    def list_jobs(
        self,
        *,
        source_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        jobs = list(self._jobs.values())
        if source_id is not None:
            jobs = [item for item in jobs if item["source_id"] == source_id]
        if status is not None:
            jobs = [item for item in jobs if item["status"] == status]
        return deepcopy(jobs)

    def quarantine_item(
        self,
        *,
        job_id: str,
        source_id: str,
        reason: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        item_id = str(uuid4())
        item = {
            "quarantine_id": item_id,
            "job_id": job_id,
            "source_id": source_id,
            "reason": reason,
            "payload": deepcopy(payload),
            "created_at": now_iso(),
            "replayed": False,
            "replayed_at": None,
        }
        self._quarantine[item_id] = item
        return deepcopy(item)

    def list_quarantine(
        self,
        *,
        source_id: str | None = None,
        replayed: bool | None = None,
    ) -> list[dict[str, Any]]:
        items = list(self._quarantine.values())
        if source_id is not None:
            items = [item for item in items if item["source_id"] == source_id]
        if replayed is not None:
            items = [item for item in items if item["replayed"] is replayed]
        return deepcopy(items)

    def mark_quarantine_replayed(
        self,
        quarantine_id: str,
    ) -> dict[str, Any] | None:
        item = self._quarantine.get(quarantine_id)
        if item is None:
            return None
        item["replayed"] = True
        item["replayed_at"] = now_iso()
        return deepcopy(item)
