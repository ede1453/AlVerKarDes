from app.domains.events.event_bus_service import EventBusService
from app.domains.events.event_repository_factory import get_event_repository
from app.domains.llm_provider_health.provider_health_service import ProviderHealthService
from app.domains.provider_scheduler.provider_scheduler_models import (
    ProviderScheduleCreate,
    create_provider_schedule,
)
from app.domains.provider_scheduler.provider_scheduler_repository import (
    InMemoryProviderSchedulerRepository,
)
from app.domains.provider_scheduler.provider_scheduler_serializer import (
    serialize_provider_schedule,
)

DEFAULT_STALE_LOCK_SECONDS = 300
DEFAULT_RUN_ONCE_WORKER_ID = "run-once"


class ProviderSchedulerService:
    def __init__(
        self,
        repository: InMemoryProviderSchedulerRepository | None = None,
        provider_health_service: ProviderHealthService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.repository = repository or InMemoryProviderSchedulerRepository()
        self.provider_health_service = provider_health_service or ProviderHealthService()
        self.event_bus_service = event_bus_service or EventBusService(
            repository=get_event_repository()
        )

    async def create(self, payload: dict):
        schedule = create_provider_schedule(
            ProviderScheduleCreate(
                name=payload["name"],
                providers=payload.get("providers", ["mock", "openai", "local"]),
                interval_seconds=payload.get("interval_seconds", 60),
                enabled=payload.get("enabled", True),
            )
        )
        saved = await self.repository.save(schedule)
        return serialize_provider_schedule(saved)

    async def get(self, schedule_id: str):
        schedule = await self.repository.get(schedule_id)
        if schedule is None:
            return None
        return serialize_provider_schedule(schedule)

    async def list(self):
        return [serialize_provider_schedule(schedule) for schedule in await self.repository.list()]

    async def claim_next(
        self,
        *,
        worker_id: str,
        stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS,
        schedule_id: str | None = None,
    ):
        # SCALE-004: atomic cross-worker claim (SELECT FOR UPDATE SKIP
        # LOCKED on the DB-backed repository). schedule_id=None picks the
        # next enabled, due schedule (a due-schedule poller's primitive);
        # schedule_id set locks one specific schedule (used internally by
        # run_once as a guard). A schedule whose worker crashed mid-check
        # becomes reclaimable once its lock is older than
        # stale_lock_seconds (see db_models.py::ProviderScheduleModel).
        schedule = await self.repository.claim(
            schedule_id=schedule_id,
            worker_id=worker_id,
            stale_lock_seconds=stale_lock_seconds,
        )
        if schedule is None:
            return None
        return serialize_provider_schedule(schedule)

    async def complete(self, schedule_id: str, result: dict):
        schedule = await self.repository.complete_run(schedule_id, result)
        if schedule is None:
            return None

        event = self._publish_run_event(schedule, result)
        return {
            "schedule": serialize_provider_schedule(schedule),
            "result": result,
            "event": event,
        }

    async def run_once(self, schedule_id: str, worker_id: str = DEFAULT_RUN_ONCE_WORKER_ID):
        existing = await self.repository.get(schedule_id)
        if existing is None:
            return None

        claimed = await self.repository.claim(
            schedule_id=schedule_id,
            worker_id=worker_id,
            stale_lock_seconds=DEFAULT_STALE_LOCK_SECONDS,
        )
        if claimed is None:
            # SCALE-004: another caller already holds a fresh lock on this
            # exact schedule (a concurrent run_once, or a due-schedule
            # poller mid-check) -- skip instead of double-executing the
            # health check. The pre-SCALE-004 code had no such guard: two
            # concurrent callers would both run and both overwrite
            # last_result/last_run_at.
            result = {"status": "SKIPPED", "reason": "ALREADY_RUNNING"}
            return {
                "schedule": serialize_provider_schedule(existing),
                "result": result,
                "event": None,
            }

        if not claimed.enabled:
            result = {"status": "SKIPPED", "reason": "SCHEDULE_DISABLED"}
        else:
            result = self.provider_health_service.check(
                {
                    "providers": claimed.providers,
                    "include_external_boundaries": True,
                }
            )

        updated = await self.repository.complete_run(schedule_id, result)
        event = self._publish_run_event(updated, result)

        return {
            "schedule": serialize_provider_schedule(updated),
            "result": result,
            "event": event,
        }

    def _publish_run_event(self, schedule, result: dict):
        return self.event_bus_service.publish(
            {
                "event_type": "provider_health.checked",
                "source": "provider_scheduler",
                "payload": {
                    "schedule_id": schedule.id,
                    "schedule_name": schedule.name,
                    "result_status": result.get("status"),
                    "providers": schedule.providers,
                },
                "metadata": {
                    "event_version": "event_v1",
                },
            }
        )

    async def clear(self):
        await self.repository.clear()
        return {"cleared": True}
