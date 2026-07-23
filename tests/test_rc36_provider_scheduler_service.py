import pytest

from app.domains.provider_scheduler.provider_scheduler_service import ProviderSchedulerService


@pytest.mark.asyncio
async def test_provider_scheduler_service_create_and_run_once():
    service = ProviderSchedulerService()
    schedule = await service.create({"name": "provider-health", "providers": ["mock"], "interval_seconds": 30})

    result = await service.run_once(schedule["id"])

    assert result["result"]["status"] == "HEALTHY"
    assert result["event"]["event_type"] == "provider_health.checked"
    assert result["schedule"]["last_run_at"] is not None
    assert result["schedule"]["locked_by"] is None


@pytest.mark.asyncio
async def test_provider_scheduler_service_disabled_schedule_skips():
    service = ProviderSchedulerService()
    schedule = await service.create({"name": "disabled", "providers": ["mock"], "enabled": False})

    result = await service.run_once(schedule["id"])

    assert result["result"]["status"] == "SKIPPED"
    assert result["result"]["reason"] == "SCHEDULE_DISABLED"
