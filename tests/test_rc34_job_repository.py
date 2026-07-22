import pytest

from app.domains.jobs.job_models import JobCreate, create_job_record
from app.domains.jobs.job_repository import InMemoryJobRepository


@pytest.mark.asyncio
async def test_job_repository_saves_and_gets_job():
    repository = InMemoryJobRepository()
    job = create_job_record(JobCreate(job_type="noop", payload={"x": 1}))

    await repository.save(job)
    found = await repository.get(job.id)

    assert found.id == job.id
    assert found.status == "PENDING"


@pytest.mark.asyncio
async def test_job_repository_marks_completed():
    repository = InMemoryJobRepository()
    job = await repository.save(create_job_record(JobCreate(job_type="noop")))

    await repository.mark_running(job.id)
    completed = await repository.mark_completed(job.id, {"status": "ok"})

    assert completed.status == "COMPLETED"
    assert completed.result == {"status": "ok"}
    assert completed.locked_by is None
    assert completed.locked_at is None


@pytest.mark.asyncio
async def test_job_repository_claim_next_locks_a_pending_job():
    repository = InMemoryJobRepository()
    job = await repository.save(create_job_record(JobCreate(job_type="noop")))

    claimed = await repository.claim_next(worker_id="worker-1")

    assert claimed.id == job.id
    assert claimed.status == "RUNNING"
    assert claimed.locked_by == "worker-1"


@pytest.mark.asyncio
async def test_job_repository_claim_next_skips_an_actively_locked_job():
    repository = InMemoryJobRepository()
    await repository.save(create_job_record(JobCreate(job_type="noop")))
    await repository.claim_next(worker_id="worker-1")

    second_claim = await repository.claim_next(worker_id="worker-2")

    assert second_claim is None
