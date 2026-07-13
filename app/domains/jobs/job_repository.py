from datetime import datetime, timezone

from app.domains.jobs.job_models import JobRecord


class InMemoryJobRepository:
    def __init__(self):
        self._jobs: dict[str, JobRecord] = {}

    def save(self, job: JobRecord) -> JobRecord:
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str):
        return self._jobs.get(job_id)

    def list_recent(self, limit: int = 20):
        return sorted(
            self._jobs.values(),
            key=lambda job: job.created_at,
            reverse=True,
        )[:limit]

    def mark_running(self, job_id: str):
        job = self._jobs[job_id]
        job.status = "RUNNING"
        job.updated_at = datetime.now(timezone.utc)
        return job

    def mark_completed(self, job_id: str, result: dict):
        job = self._jobs[job_id]
        job.status = "COMPLETED"
        job.result = result
        job.error = None
        job.updated_at = datetime.now(timezone.utc)
        return job

    def mark_failed(self, job_id: str, error: str):
        job = self._jobs[job_id]
        job.status = "FAILED"
        job.error = error
        job.updated_at = datetime.now(timezone.utc)
        return job
