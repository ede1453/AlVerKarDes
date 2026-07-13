from app.domains.provider_scheduler.provider_scheduler_models import ProviderScheduleCreate, create_provider_schedule
from app.domains.provider_scheduler.provider_scheduler_repository import InMemoryProviderSchedulerRepository


def test_provider_scheduler_repository_save_and_get():
    repository = InMemoryProviderSchedulerRepository()
    schedule = create_provider_schedule(ProviderScheduleCreate(name="default"))

    repository.save(schedule)

    assert repository.get(schedule.id).name == "default"


def test_provider_scheduler_repository_update_result():
    repository = InMemoryProviderSchedulerRepository()
    schedule = repository.save(create_provider_schedule(ProviderScheduleCreate(name="default")))

    updated = repository.update_result(schedule.id, {"status": "DEGRADED"})

    assert updated.last_result == {"status": "DEGRADED"}
    assert updated.last_run_at is not None
