from app.domains.jobs.job_executor import JobExecutor
from app.domains.jobs.job_models import JobCreate, create_job_record
from app.domains.jobs.job_repository import InMemoryJobRepository
from app.domains.jobs.job_serializer import serialize_job

DEFAULT_STALE_LOCK_SECONDS = 300


class JobQueueService:
    def __init__(
        self,
        repository: InMemoryJobRepository | None = None,
        executor: JobExecutor | None = None,
    ):
        self.repository = repository or InMemoryJobRepository()
        self.executor = executor or JobExecutor()

    async def enqueue(self, payload: dict):
        job = create_job_record(
            JobCreate(
                job_type=payload["job_type"],
                payload=payload.get("payload", {}),
            )
        )

        saved = await self.repository.save(job)
        return serialize_job(saved)

    async def run_now(self, payload: dict):
        job_data = await self.enqueue(payload)
        job_id = job_data["id"]

        await self.repository.mark_running(job_id)

        try:
            result = self.executor.execute(
                job_type=payload["job_type"],
                payload=payload.get("payload", {}),
            )
        except Exception as exc:
            job = await self.repository.mark_failed(job_id, str(exc))
            return serialize_job(job)

        job = await self.repository.mark_completed(job_id, result)
        return serialize_job(job)

    async def claim_next(self, *, worker_id: str, stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS):
        # SCALE-003: atomic cross-worker claim (SELECT FOR UPDATE SKIP
        # LOCKED on the DB-backed repository) -- a job whose worker crashed
        # without completing/failing it becomes reclaimable once its lock
        # is older than stale_lock_seconds (see db_models.py::JobModel).
        job = await self.repository.claim_next(
            worker_id=worker_id,
            stale_lock_seconds=stale_lock_seconds,
        )
        if job is None:
            return None
        return serialize_job(job)

    async def complete(self, job_id: str, result: dict):
        job = await self.repository.mark_completed(job_id, result)
        if job is None:
            return None
        return serialize_job(job)

    async def fail(self, job_id: str, error: str):
        job = await self.repository.mark_failed(job_id, error)
        if job is None:
            return None
        return serialize_job(job)

    async def get(self, job_id: str):
        job = await self.repository.get(job_id)
        if job is None:
            return None
        return serialize_job(job)

    async def list_recent(self, limit: int = 20):
        return [serialize_job(job) for job in await self.repository.list_recent(limit=limit)]
