from app.domains.jobs.job_queue_service import JobQueueService


def test_job_queue_service_enqueue_creates_pending_job():
    service = JobQueueService()

    job = service.enqueue({"job_type": "noop", "payload": {"x": 1}})

    assert job["status"] == "PENDING"
    assert service.get(job["id"])["id"] == job["id"]


def test_job_queue_service_run_now_completes_job():
    service = JobQueueService()

    job = service.run_now({"job_type": "noop", "payload": {"x": 1}})

    assert job["status"] == "COMPLETED"
    assert job["result"]["echo"] == {"x": 1}
