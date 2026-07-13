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

    def create(self, payload: dict):
        schedule = create_provider_schedule(
            ProviderScheduleCreate(
                name=payload["name"],
                providers=payload.get("providers", ["mock", "openai", "local"]),
                interval_seconds=payload.get("interval_seconds", 60),
                enabled=payload.get("enabled", True),
            )
        )
        return serialize_provider_schedule(self.repository.save(schedule))

    def get(self, schedule_id: str):
        schedule = self.repository.get(schedule_id)
        if schedule is None:
            return None
        return serialize_provider_schedule(schedule)

    def list(self):
        return [serialize_provider_schedule(schedule) for schedule in self.repository.list()]

    def run_once(self, schedule_id: str):
        schedule = self.repository.get(schedule_id)
        if schedule is None:
            return None

        if not schedule.enabled:
            result = {
                "status": "SKIPPED",
                "reason": "SCHEDULE_DISABLED",
            }
        else:
            result = self.provider_health_service.check(
                {
                    "providers": schedule.providers,
                    "include_external_boundaries": True,
                }
            )

        updated = self.repository.update_result(schedule_id, result)

        event = self.event_bus_service.publish(
            {
                "event_type": "provider_health.checked",
                "source": "provider_scheduler",
                "payload": {
                    "schedule_id": schedule_id,
                    "schedule_name": schedule.name,
                    "result_status": result.get("status"),
                    "providers": schedule.providers,
                },
                "metadata": {
                    "event_version": "event_v1",
                },
            }
        )

        return {
            "schedule": serialize_provider_schedule(updated),
            "result": result,
            "event": event,
        }

    def clear(self):
        self.repository.clear()
        return {"cleared": True}
