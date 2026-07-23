from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.provider_scheduler.db_models import ProviderScheduleModel
from app.domains.provider_scheduler.provider_scheduler_models import ProviderScheduleRecord


class InMemoryProviderSchedulerRepository:
    """Plain in-memory test double (async methods for interface parity with
    ProviderSchedulerDBRepository -- same pattern as job_repository.py's
    InMemoryJobRepository, SCALE-003). Not used by the API anymore
    (SCALE-004); kept for unit tests that want a repository without a real
    database. claim() here is NOT safe across processes (a plain dict has
    no cross-process visibility or locking) -- it exists only so
    ProviderSchedulerService's default construction still has a working
    claim path for single-process tests."""

    def __init__(self):
        self._schedules: dict[str, ProviderScheduleRecord] = {}

    async def save(self, schedule: ProviderScheduleRecord) -> ProviderScheduleRecord:
        self._schedules[schedule.id] = schedule
        return schedule

    async def get(self, schedule_id: str):
        return self._schedules.get(schedule_id)

    async def list(self):
        return list(self._schedules.values())

    def _is_locked(self, schedule: ProviderScheduleRecord, stale_cutoff: datetime) -> bool:
        return schedule.status == "RUNNING" and schedule.locked_at is not None and schedule.locked_at >= stale_cutoff

    async def claim(self, *, schedule_id: str | None, worker_id: str, stale_lock_seconds: int):
        stale_cutoff = datetime.now(timezone.utc) - timedelta(seconds=stale_lock_seconds)
        now = datetime.now(timezone.utc)

        if schedule_id is not None:
            schedule = self._schedules.get(schedule_id)
            if schedule is None or self._is_locked(schedule, stale_cutoff):
                return None
            candidates = [schedule]
        else:
            due = [
                schedule
                for schedule in self._schedules.values()
                if schedule.enabled
                and not self._is_locked(schedule, stale_cutoff)
                and (
                    schedule.last_run_at is None
                    or now >= schedule.last_run_at + timedelta(seconds=schedule.interval_seconds)
                )
            ]
            candidates = sorted(due, key=lambda schedule: schedule.created_at)[:1]

        if not candidates:
            return None

        schedule = candidates[0]
        schedule.status = "RUNNING"
        schedule.locked_by = worker_id
        schedule.locked_at = now
        return schedule

    async def complete_run(self, schedule_id: str, result: dict):
        schedule = self._schedules.get(schedule_id)
        if schedule is None:
            return None

        schedule.last_run_at = datetime.now(timezone.utc)
        schedule.last_result = result
        schedule.locked_by = None
        schedule.locked_at = None
        schedule.status = "ACTIVE" if schedule.enabled else "DISABLED"
        return schedule

    async def clear(self):
        self._schedules.clear()


def _to_schedule(row: ProviderScheduleModel) -> ProviderScheduleRecord:
    return ProviderScheduleRecord(
        id=str(row.id),
        name=row.name,
        providers=list(row.providers or []),
        interval_seconds=row.interval_seconds,
        enabled=row.enabled,
        status=row.status,
        created_at=row.created_at,
        last_run_at=row.last_run_at,
        last_result=row.last_result,
        locked_by=row.locked_by,
        locked_at=row.locked_at,
    )


class ProviderSchedulerDBRepository:
    """Postgres-backed repository (SCALE-004).

    Before this, ProviderSchedulerService only ever wrote to an in-memory
    dict (InMemoryProviderSchedulerRepository) -- worker-process-local,
    invisible to other workers, and lost on restart. This repository
    persists to the real provider_schedules table (migration
    0023_provider_schedules).

    Unlike jobs (SCALE-003), a schedule is recurring, not one-shot: the
    original code had no claim mechanism at all -- run_once() just read the
    row and executed inline, so two concurrent callers racing on the same
    schedule_id (two workers both handling an explicit "run this schedule
    now" request, or a due-schedule poller running on more than one worker)
    would both execute the same health check at once. claim() closes that
    gap with the same SELECT ... FOR UPDATE SKIP LOCKED primitive as
    JobDBRepository.claim_next() -- one call locks the row (or the next due
    row) so a second concurrent claim on it is skipped, not double-claimed.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, schedule: ProviderScheduleRecord) -> ProviderScheduleRecord:
        row = ProviderScheduleModel(
            id=UUID(schedule.id),
            name=schedule.name,
            providers=list(schedule.providers),
            interval_seconds=schedule.interval_seconds,
            enabled=schedule.enabled,
            status=schedule.status,
            created_at=schedule.created_at,
            last_run_at=schedule.last_run_at,
            last_result=schedule.last_result,
            locked_by=schedule.locked_by,
            locked_at=schedule.locked_at,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return _to_schedule(row)

    async def get(self, schedule_id: str) -> ProviderScheduleRecord | None:
        try:
            key = UUID(schedule_id)
        except ValueError:
            return None

        row = await self.db.get(ProviderScheduleModel, key)
        if row is None:
            return None
        return _to_schedule(row)

    async def list(self) -> list[ProviderScheduleRecord]:
        result = await self.db.execute(
            select(ProviderScheduleModel).order_by(ProviderScheduleModel.created_at)
        )
        return [_to_schedule(row) for row in result.scalars().all()]

    async def claim(
        self, *, schedule_id: str | None, worker_id: str, stale_lock_seconds: int
    ) -> ProviderScheduleRecord | None:
        stale_cutoff = datetime.now(timezone.utc) - timedelta(seconds=stale_lock_seconds)
        not_actively_locked = or_(
            ProviderScheduleModel.status != "RUNNING",
            ProviderScheduleModel.locked_at < stale_cutoff,
        )

        if schedule_id is not None:
            try:
                key = UUID(schedule_id)
            except ValueError:
                return None

            stmt = (
                select(ProviderScheduleModel)
                .where(ProviderScheduleModel.id == key, not_actively_locked)
                .with_for_update(skip_locked=True)
            )
        else:
            now = datetime.now(timezone.utc)
            due = or_(
                ProviderScheduleModel.last_run_at.is_(None),
                ProviderScheduleModel.last_run_at
                + func.make_interval(0, 0, 0, 0, 0, 0, ProviderScheduleModel.interval_seconds)
                <= now,
            )
            stmt = (
                select(ProviderScheduleModel)
                .where(
                    ProviderScheduleModel.enabled.is_(True),
                    not_actively_locked,
                    due,
                )
                .order_by(ProviderScheduleModel.created_at)
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
        await self.db.commit()
        await self.db.refresh(row)
        return _to_schedule(row)

    async def complete_run(self, schedule_id: str, result: dict) -> ProviderScheduleRecord | None:
        try:
            key = UUID(schedule_id)
        except ValueError:
            return None

        row = await self.db.get(ProviderScheduleModel, key)
        if row is None:
            return None

        row.last_run_at = datetime.now(timezone.utc)
        row.last_result = result
        row.locked_by = None
        row.locked_at = None
        row.status = "ACTIVE" if row.enabled else "DISABLED"
        await self.db.commit()
        await self.db.refresh(row)
        return _to_schedule(row)

    async def clear(self) -> None:
        result = await self.db.execute(select(ProviderScheduleModel))
        for row in result.scalars().all():
            await self.db.delete(row)
        await self.db.commit()
