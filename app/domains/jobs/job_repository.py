from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.jobs.db_models import JobModel
from app.domains.jobs.job_models import JobRecord


class InMemoryJobRepository:
    """Plain in-memory test double (async methods for interface parity with
    JobDBRepository -- same pattern as watchlist_repository.py's
    InMemoryWatchlistRepository, CLIENT-002e). Not used by the API anymore
    (SCALE-003); kept for unit tests that want a repository without a real
    database. claim_next() here is NOT safe across processes (a plain dict
    has no cross-process visibility or locking) -- it exists only so
    JobQueueService's default construction still has a working claim path
    for single-process tests."""

    def __init__(self):
        self._jobs: dict[str, JobRecord] = {}

    async def save(self, job: JobRecord) -> JobRecord:
        self._jobs[job.id] = job
        return job

    async def get(self, job_id: str):
        return self._jobs.get(job_id)

    async def list_recent(self, limit: int = 20):
        return sorted(
            self._jobs.values(),
            key=lambda job: job.created_at,
            reverse=True,
        )[:limit]

    async def claim_next(self, *, worker_id: str, stale_lock_seconds: int = 300):
        stale_cutoff = datetime.now(timezone.utc) - timedelta(seconds=stale_lock_seconds)
        candidates = sorted(self._jobs.values(), key=lambda job: job.created_at)

        for job in candidates:
            is_stale_running = job.status == "RUNNING" and job.updated_at < stale_cutoff
            if job.status == "PENDING" or is_stale_running:
                job.status = "RUNNING"
                job.locked_by = worker_id
                job.locked_at = datetime.now(timezone.utc)
                job.updated_at = job.locked_at
                return job

        return None

    async def mark_running(self, job_id: str):
        job = self._jobs[job_id]
        job.status = "RUNNING"
        job.updated_at = datetime.now(timezone.utc)
        return job

    async def mark_completed(self, job_id: str, result: dict):
        job = self._jobs[job_id]
        job.status = "COMPLETED"
        job.result = result
        job.error = None
        job.locked_by = None
        job.locked_at = None
        job.updated_at = datetime.now(timezone.utc)
        return job

    async def mark_failed(self, job_id: str, error: str):
        job = self._jobs[job_id]
        job.status = "FAILED"
        job.error = error
        job.locked_by = None
        job.locked_at = None
        job.updated_at = datetime.now(timezone.utc)
        return job


def _to_job(row: JobModel) -> JobRecord:
    return JobRecord(
        id=str(row.id),
        job_type=row.job_type,
        status=row.status,
        payload=dict(row.payload or {}),
        result=row.result,
        error=row.error,
        locked_by=row.locked_by,
        locked_at=row.locked_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class JobDBRepository:
    """Postgres-backed repository (SCALE-003).

    Before this, JobQueueService only ever wrote to an in-memory dict
    (InMemoryJobRepository) -- worker-process-local, invisible to other
    workers, and lost on restart. This repository persists to the real
    jobs table (migration 0022_jobs). claim_next() uses
    SELECT ... FOR UPDATE SKIP LOCKED, so two concurrent workers racing for
    the same row never both claim it: Postgres's row lock makes one of them
    skip the locked row and move to the next candidate (or find none)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, job: JobRecord) -> JobRecord:
        row = JobModel(
            id=UUID(job.id),
            job_type=job.job_type,
            status=job.status,
            payload=dict(job.payload),
            result=job.result,
            error=job.error,
            locked_by=job.locked_by,
            locked_at=job.locked_at,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return _to_job(row)

    async def get(self, job_id: str) -> JobRecord | None:
        try:
            key = UUID(job_id)
        except ValueError:
            return None

        row = await self.db.get(JobModel, key)
        if row is None:
            return None
        return _to_job(row)

    async def list_recent(self, limit: int = 20) -> list[JobRecord]:
        result = await self.db.execute(
            select(JobModel).order_by(JobModel.created_at.desc()).limit(limit)
        )
        return [_to_job(row) for row in result.scalars().all()]

    async def claim_next(self, *, worker_id: str, stale_lock_seconds: int = 300) -> JobRecord | None:
        stale_cutoff = datetime.now(timezone.utc) - timedelta(seconds=stale_lock_seconds)

        stmt = (
            select(JobModel)
            .where(
                or_(
                    JobModel.status == "PENDING",
                    and_(JobModel.status == "RUNNING", JobModel.locked_at < stale_cutoff),
                )
            )
            .order_by(JobModel.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(stmt)
        row = result.scalars().first()

        if row is None:
            await self.db.commit()
            return None

        row.status = "RUNNING"
        row.locked_by = worker_id
        row.locked_at = datetime.now(timezone.utc)
        row.updated_at = row.locked_at
        await self.db.commit()
        await self.db.refresh(row)
        return _to_job(row)

    async def mark_running(self, job_id: str) -> JobRecord | None:
        row = await self.db.get(JobModel, UUID(job_id))
        if row is None:
            return None

        row.status = "RUNNING"
        row.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(row)
        return _to_job(row)

    async def mark_completed(self, job_id: str, result: dict) -> JobRecord | None:
        row = await self.db.get(JobModel, UUID(job_id))
        if row is None:
            return None

        row.status = "COMPLETED"
        row.result = result
        row.error = None
        row.locked_by = None
        row.locked_at = None
        row.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(row)
        return _to_job(row)

    async def mark_failed(self, job_id: str, error: str) -> JobRecord | None:
        row = await self.db.get(JobModel, UUID(job_id))
        if row is None:
            return None

        row.status = "FAILED"
        row.error = error
        row.locked_by = None
        row.locked_at = None
        row.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(row)
        return _to_job(row)
