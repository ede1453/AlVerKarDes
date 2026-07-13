from datetime import datetime, timedelta, timezone

from app.domains.commerce_ingestion.operations import ConnectorOperationsService


def test_rc123_register_and_find_due_schedule():
    service = ConnectorOperationsService()
    result = service.register_schedule(
        schedule_id="amazon-hourly",
        source_id="amazon-de",
        interval_minutes=60,
    )
    future = (
        datetime.now(timezone.utc)
        + timedelta(minutes=61)
    ).isoformat()
    due = service.list_due_schedules(at_time=future)
    assert result["registered"] is True
    assert due["due_count"] == 1

def test_rc123_mark_run_moves_next_run():
    service = ConnectorOperationsService()
    service.register_schedule(
        schedule_id="amazon-hourly",
        source_id="amazon-de",
        interval_minutes=60,
    )
    result = service.mark_schedule_run("amazon-hourly")
    assert result["updated"] is True
    assert result["schedule"]["last_run_at"] is not None
