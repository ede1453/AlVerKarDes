from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc86_scheduler_status_defaults_to_idle():
    service = NotificationOutboxService()

    result = service.get_scheduler_status()

    assert result["status"] == "IDLE"
    assert result["job_count"] == 0
    assert result["metadata"]["scheduler_version"] == "background_job_scheduler_v1"


def test_rc86_register_scheduled_job():
    service = NotificationOutboxService()

    result = service.register_scheduled_job(
        job_name="notification-retry-scheduler",
        interval_seconds=60,
        enabled=True,
    )

    assert result["registered"] is True
    assert result["job"]["job_name"] == "notification-retry-scheduler"
    assert result["job"]["interval_seconds"] == 60
    assert result["job"]["enabled"] is True


def test_rc86_scheduler_status_reports_registered_jobs():
    service = NotificationOutboxService()

    service.register_scheduled_job(
        job_name="notification-retry-scheduler",
        interval_seconds=60,
        enabled=True,
    )
    service.register_scheduled_job(
        job_name="notification-digest-scheduler",
        interval_seconds=300,
        enabled=False,
    )

    result = service.get_scheduler_status()

    assert result["status"] == "RUNNING"
    assert result["job_count"] == 2
    assert result["enabled_job_count"] == 1


def test_rc86_run_scheduled_job_updates_execution_state():
    service = NotificationOutboxService()

    service.register_scheduled_job(
        job_name="notification-retry-scheduler",
        interval_seconds=60,
        enabled=True,
    )

    result = service.run_scheduled_job(
        job_name="notification-retry-scheduler"
    )

    assert result["executed"] is True
    assert result["job"]["run_count"] == 1
    assert result["job"]["last_run_at"] is not None


def test_rc86_disabled_job_is_not_executed():
    service = NotificationOutboxService()

    service.register_scheduled_job(
        job_name="notification-digest-scheduler",
        interval_seconds=300,
        enabled=False,
    )

    result = service.run_scheduled_job(
        job_name="notification-digest-scheduler"
    )

    assert result["executed"] is False
    assert result["reason"] == "JOB_DISABLED"
