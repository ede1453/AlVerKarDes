from datetime import datetime, timedelta, timezone

import pytest

from app.domains.provider_scheduler.provider_scheduler_models import ProviderScheduleCreate, create_provider_schedule
from app.domains.provider_scheduler.provider_scheduler_repository import InMemoryProviderSchedulerRepository


@pytest.mark.asyncio
async def test_provider_scheduler_repository_save_and_get():
    repository = InMemoryProviderSchedulerRepository()
    schedule = create_provider_schedule(ProviderScheduleCreate(name="default"))

    await repository.save(schedule)

    found = await repository.get(schedule.id)
    assert found.name == "default"


@pytest.mark.asyncio
async def test_provider_scheduler_repository_claim_then_complete_run():
    repository = InMemoryProviderSchedulerRepository()
    schedule = await repository.save(create_provider_schedule(ProviderScheduleCreate(name="default")))

    claimed = await repository.claim(schedule_id=schedule.id, worker_id="worker-1", stale_lock_seconds=300)
    assert claimed.status == "RUNNING"
    assert claimed.locked_by == "worker-1"

    updated = await repository.complete_run(schedule.id, {"status": "DEGRADED"})

    assert updated.last_result == {"status": "DEGRADED"}
    assert updated.last_run_at is not None
    assert updated.status == "ACTIVE"
    assert updated.locked_by is None
    assert updated.locked_at is None


@pytest.mark.asyncio
async def test_provider_scheduler_repository_claim_skips_actively_locked_schedule():
    repository = InMemoryProviderSchedulerRepository()
    schedule = await repository.save(create_provider_schedule(ProviderScheduleCreate(name="default")))
    await repository.claim(schedule_id=schedule.id, worker_id="worker-1", stale_lock_seconds=300)

    second_claim = await repository.claim(schedule_id=schedule.id, worker_id="worker-2", stale_lock_seconds=300)

    assert second_claim is None


@pytest.mark.asyncio
async def test_provider_scheduler_repository_claim_due_picks_only_enabled_and_elapsed():
    repository = InMemoryProviderSchedulerRepository()
    due = await repository.save(
        create_provider_schedule(ProviderScheduleCreate(name="due", interval_seconds=1))
    )
    not_due = await repository.save(
        create_provider_schedule(ProviderScheduleCreate(name="not-due", interval_seconds=3600))
    )
    disabled = await repository.save(
        create_provider_schedule(ProviderScheduleCreate(name="disabled", enabled=False))
    )
    # not_due/disabled already ran "just now" -- their interval hasn't
    # elapsed, so claim(schedule_id=None) (the due-scan path) must skip them.
    await repository.complete_run(not_due.id, {"status": "HEALTHY"})
    await repository.complete_run(disabled.id, {"status": "HEALTHY"})

    claimed = await repository.claim(schedule_id=None, worker_id="poller-1", stale_lock_seconds=300)

    assert claimed.id == due.id
    assert claimed.status == "RUNNING"


@pytest.mark.asyncio
async def test_provider_scheduler_repository_claim_due_returns_none_when_nothing_due():
    repository = InMemoryProviderSchedulerRepository()
    schedule = await repository.save(
        create_provider_schedule(ProviderScheduleCreate(name="not-due-yet", interval_seconds=3600))
    )
    await repository.complete_run(schedule.id, {"status": "HEALTHY"})

    claimed = await repository.claim(schedule_id=None, worker_id="poller-1", stale_lock_seconds=300)

    assert claimed is None


@pytest.mark.asyncio
async def test_provider_scheduler_repository_claim_recovers_stale_lock():
    repository = InMemoryProviderSchedulerRepository()
    schedule = await repository.save(create_provider_schedule(ProviderScheduleCreate(name="default")))
    claimed = await repository.claim(schedule_id=schedule.id, worker_id="worker-1", stale_lock_seconds=300)
    # Simulate an abandoned claim: worker-1 crashed mid-check, never called
    # complete_run(), and its lock is now older than the stale-lock window.
    claimed.locked_at = datetime.now(timezone.utc) - timedelta(seconds=301)

    recovered = await repository.claim(schedule_id=schedule.id, worker_id="worker-2", stale_lock_seconds=300)

    assert recovered is not None
    assert recovered.locked_by == "worker-2"
