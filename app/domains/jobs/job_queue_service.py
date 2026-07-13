from app.domains.jobs.job_executor import JobExecutor
from app.domains.jobs.job_models import JobCreate, create_job_record
from app.domains.jobs.job_repository import InMemoryJobRepository
from app.domains.jobs.job_serializer import serialize_job


class JobQueueService:
    def __init__(
        self,
        repository: InMemoryJobRepository | None = None,
        executor: JobExecutor | None = None,
    ):
        self.repository = repository or InMemoryJobRepository()
        self.executor = executor or JobExecutor()

    def enqueue(self, payload: dict):
        job = create_job_record(
            JobCreate(
                job_type=payload["job_type"],
                payload=payload.get("payload", {}),
            )
        )

        saved = self.repository.save(job)
        return serialize_job(saved)

    def run_now(self, payload: dict):
        job_data = self.enqueue(payload)
        job_id = job_data["id"]

        self.repository.mark_running(job_id)

        try:
            result = self.executor.execute(
                job_type=payload["job_type"],
                payload=payload.get("payload", {}),
            )
        except Exception as exc:
            job = self.repository.mark_failed(job_id, str(exc))
            return serialize_job(job)

        job = self.repository.mark_completed(job_id, result)
        return serialize_job(job)

    def get(self, job_id: str):
        job = self.repository.get(job_id)
        if job is None:
            return None
        return serialize_job(job)

    def list_recent(self, limit: int = 20):
        return [serialize_job(job) for job in self.repository.list_recent(limit=limit)]
