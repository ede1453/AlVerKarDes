from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class JobCreate:
    job_type: str
    payload: dict = field(default_factory=dict)


@dataclass
class JobRecord:
    id: str
    job_type: str
    status: str
    payload: dict
    result: dict | None
    error: str | None
    created_at: datetime
    updated_at: datetime


def create_job_record(data: JobCreate) -> JobRecord:
    now = datetime.now(timezone.utc)
    return JobRecord(
        id=str(uuid4()),
        job_type=data.job_type,
        status="PENDING",
        payload=dict(data.payload),
        result=None,
        error=None,
        created_at=now,
        updated_at=now,
    )
