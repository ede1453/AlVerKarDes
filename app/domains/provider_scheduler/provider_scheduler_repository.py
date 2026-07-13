from datetime import datetime, timezone

from app.domains.provider_scheduler.provider_scheduler_models import ProviderScheduleRecord


class InMemoryProviderSchedulerRepository:
    def __init__(self):
        self._schedules: dict[str, ProviderScheduleRecord] = {}

    def save(self, schedule: ProviderScheduleRecord) -> ProviderScheduleRecord:
        self._schedules[schedule.id] = schedule
        return schedule

    def get(self, schedule_id: str):
        return self._schedules.get(schedule_id)

    def list(self):
        return list(self._schedules.values())

    def update_result(self, schedule_id: str, result: dict):
        schedule = self._schedules[schedule_id]
        schedule.last_run_at = datetime.now(timezone.utc)
        schedule.last_result = result
        schedule.status = "ACTIVE" if schedule.enabled else "DISABLED"
        return schedule

    def clear(self):
        self._schedules.clear()
