from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc89_instance_registry_starts_empty():
    service = NotificationOutboxService()

    result = service.get_instance_status()

    assert result["instance_count"] == 0
    assert result["healthy_instance_count"] == 0
    assert result["total_capacity"] == 0
    assert result["metadata"]["scaling_version"] == "horizontal_scaling_v1"


def test_rc89_register_instance():
    service = NotificationOutboxService()

    result = service.register_instance(
        instance_id="api-1",
        capacity=100,
        healthy=True,
    )

    assert result["registered"] is True
    assert result["instance"]["instance_id"] == "api-1"
    assert result["instance"]["capacity"] == 100
    assert result["instance"]["healthy"] is True
    assert result["instance"]["current_load"] == 0


def test_rc89_instance_status_aggregates_capacity():
    service = NotificationOutboxService()

    service.register_instance("api-1", capacity=100, healthy=True)
    service.register_instance("api-2", capacity=200, healthy=True)
    service.register_instance("api-3", capacity=50, healthy=False)

    result = service.get_instance_status()

    assert result["instance_count"] == 3
    assert result["healthy_instance_count"] == 2
    assert result["total_capacity"] == 350
    assert result["healthy_capacity"] == 300


def test_rc89_assign_load_uses_least_loaded_healthy_instance():
    service = NotificationOutboxService()

    service.register_instance("api-1", capacity=10, healthy=True)
    service.register_instance("api-2", capacity=10, healthy=True)

    first = service.assign_instance_load("request-1")
    second = service.assign_instance_load("request-2")

    assert first["assigned"] is True
    assert second["assigned"] is True
    assert first["instance"]["instance_id"] != second["instance"]["instance_id"]


def test_rc89_assignment_fails_when_no_healthy_capacity():
    service = NotificationOutboxService()

    service.register_instance("api-1", capacity=1, healthy=False)

    result = service.assign_instance_load("request-1")

    assert result["assigned"] is False
    assert result["reason"] == "NO_HEALTHY_INSTANCE_CAPACITY"


def test_rc89_release_instance_load_decrements_current_load():
    service = NotificationOutboxService()

    service.register_instance("api-1", capacity=1, healthy=True)
    assigned = service.assign_instance_load("request-1")

    result = service.release_instance_load(
        instance_id=assigned["instance"]["instance_id"],
        request_id="request-1",
    )

    assert result["released"] is True
    assert result["instance"]["current_load"] == 0
