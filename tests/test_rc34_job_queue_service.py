import pytest

from app.domains.jobs.job_queue_service import JobQueueService


@pytest.mark.asyncio
async def test_job_queue_service_enqueue_creates_pending_job():
    service = JobQueueService()

    job = await service.enqueue({"job_type": "noop", "payload": {"x": 1}})

    assert job["status"] == "PENDING"
    assert (await service.get(job["id"]))["id"] == job["id"]


@pytest.mark.asyncio
async def test_job_queue_service_run_now_completes_job():
    service = JobQueueService()

    job = await service.run_now({"job_type": "noop", "payload": {"x": 1}})

    assert job["status"] == "COMPLETED"
    assert job["result"]["echo"] == {"x": 1}


@pytest.mark.asyncio
async def test_job_queue_service_claim_next_then_complete_releases_lock():
    service = JobQueueService()
    await service.enqueue({"job_type": "noop", "payload": {"x": 1}})

    claimed = await service.claim_next(worker_id="worker-1")
    assert claimed["status"] == "RUNNING"
    assert claimed["locked_by"] == "worker-1"

    completed = await service.complete(claimed["id"], {"echo": {"x": 1}})
    assert completed["status"] == "COMPLETED"
    assert completed["locked_by"] is None


@pytest.mark.asyncio
async def test_job_queue_service_claim_next_returns_none_when_empty():
    service = JobQueueService()

    claimed = await service.claim_next(worker_id="worker-1")

    assert claimed is None
