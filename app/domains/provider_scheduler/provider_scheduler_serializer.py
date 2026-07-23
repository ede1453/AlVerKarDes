def serialize_provider_schedule(schedule):
    return {
        "id": schedule.id,
        "name": schedule.name,
        "providers": schedule.providers,
        "interval_seconds": schedule.interval_seconds,
        "enabled": schedule.enabled,
        "status": schedule.status,
        "created_at": schedule.created_at.isoformat(),
        "last_run_at": None if schedule.last_run_at is None else schedule.last_run_at.isoformat(),
        "last_result": schedule.last_result,
        "locked_by": schedule.locked_by,
        "locked_at": None if schedule.locked_at is None else schedule.locked_at.isoformat(),
    }
