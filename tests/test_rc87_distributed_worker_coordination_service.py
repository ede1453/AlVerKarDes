from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc87_worker_registry_starts_empty():
    service = NotificationOutboxService()
    result = service.get_worker_status()
    assert result["worker_count"] == 0
    assert result["active_worker_count"] == 0
    assert result["workers"] == []

def test_rc87_register_worker():
    service = NotificationOutboxService()
    result = service.register_worker("worker-1", capacity=10, enabled=True)
    assert result["registered"] is True
    assert result["worker"]["worker_id"] == "worker-1"
    assert result["worker"]["assigned_jobs"] == 0

def test_rc87_assign_job_uses_available_worker():
    service = NotificationOutboxService()
    service.register_worker("worker-1", capacity=1, enabled=True)
    result = service.assign_job_to_worker("job-1")
    assert result["assigned"] is True
    assert result["worker"]["worker_id"] == "worker-1"

def test_rc87_assignment_fails_without_worker():
    service = NotificationOutboxService()
    result = service.assign_job_to_worker("job-1")
    assert result["assigned"] is False
    assert result["reason"] == "NO_AVAILABLE_WORKER"

def test_rc87_complete_job_decrements_load():
    service = NotificationOutboxService()
    service.register_worker("worker-1", capacity=1, enabled=True)
    service.assign_job_to_worker("job-1")
    result = service.complete_worker_job("worker-1", "job-1")
    assert result["completed"] is True
    assert result["worker"]["assigned_jobs"] == 0
