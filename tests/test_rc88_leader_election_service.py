from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc88_leader_election_starts_without_leader():
    service = NotificationOutboxService()

    result = service.get_leader_status()

    assert result["leader_id"] is None
    assert result["has_leader"] is False
    assert result["metadata"]["leader_election_version"] == "leader_election_v1"


def test_rc88_first_worker_becomes_leader():
    service = NotificationOutboxService()

    result = service.acquire_leadership(
        worker_id="worker-1",
        lease_seconds=30,
    )

    assert result["acquired"] is True
    assert result["leader_id"] == "worker-1"
    assert result["lease_expires_at"] is not None


def test_rc88_second_worker_cannot_take_active_leadership():
    service = NotificationOutboxService()

    service.acquire_leadership(
        worker_id="worker-1",
        lease_seconds=30,
    )
    result = service.acquire_leadership(
        worker_id="worker-2",
        lease_seconds=30,
    )

    assert result["acquired"] is False
    assert result["reason"] == "LEADER_ALREADY_ACTIVE"
    assert result["leader_id"] == "worker-1"


def test_rc88_current_leader_can_renew_lease():
    service = NotificationOutboxService()

    service.acquire_leadership(
        worker_id="worker-1",
        lease_seconds=30,
    )
    result = service.renew_leadership(
        worker_id="worker-1",
        lease_seconds=60,
    )

    assert result["renewed"] is True
    assert result["leader_id"] == "worker-1"


def test_rc88_non_leader_cannot_renew_lease():
    service = NotificationOutboxService()

    service.acquire_leadership(
        worker_id="worker-1",
        lease_seconds=30,
    )
    result = service.renew_leadership(
        worker_id="worker-2",
        lease_seconds=60,
    )

    assert result["renewed"] is False
    assert result["reason"] == "NOT_CURRENT_LEADER"


def test_rc88_current_leader_can_release_leadership():
    service = NotificationOutboxService()

    service.acquire_leadership(
        worker_id="worker-1",
        lease_seconds=30,
    )
    result = service.release_leadership(
        worker_id="worker-1"
    )

    assert result["released"] is True
    assert result["leader_id"] is None
