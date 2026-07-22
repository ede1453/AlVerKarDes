def serialize_job(job):
    return {
        "id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "payload": job.payload,
        "result": job.result,
        "error": job.error,
        "locked_by": job.locked_by,
        "locked_at": job.locked_at.isoformat() if job.locked_at else None,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }
