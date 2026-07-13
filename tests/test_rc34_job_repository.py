from app.domains.jobs.job_models import JobCreate, create_job_record
from app.domains.jobs.job_repository import InMemoryJobRepository


def test_job_repository_saves_and_gets_job():
    repository = InMemoryJobRepository()
    job = create_job_record(JobCreate(job_type="noop", payload={"x": 1}))

    repository.save(job)
    found = repository.get(job.id)

    assert found.id == job.id
    assert found.status == "PENDING"


def test_job_repository_marks_completed():
    repository = InMemoryJobRepository()
    job = repository.save(create_job_record(JobCreate(job_type="noop")))

    repository.mark_running(job.id)
    completed = repository.mark_completed(job.id, {"status": "ok"})

    assert completed.status == "COMPLETED"
    assert completed.result == {"status": "ok"}
