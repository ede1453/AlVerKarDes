from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


async def _make_dead_letter(service: NotificationOutboxService) -> dict:
    queued = await service.enqueue(
        {
            "user_id": "rc72-user",
            "title": "RC72",
            "message": "DLQ replay audit",
            "payload": {"source": "rc72"},
        }
    )

    for _ in range(3):
        await service.claim_next(worker_id="worker-rc72")
        failed = await service.mark_failed(
            item_id=queued["id"],
            error="PROVIDER_TIMEOUT",
            next_retry_at="2000-01-01T00:00:00+00:00",
        )
        if failed["item"]["status"] != "DEAD_LETTER":
            await service.requeue_due_retries()

    return queued


async def test_rc72_replay_dead_letter_adds_audit_metadata():
    service = NotificationOutboxService()
    queued = await _make_dead_letter(service)

    replayed = await service.replay_dead_letter(
        queued["id"],
        replay_reason="manual_admin_retry",
        replayed_by="rc72-admin",
    )

    assert replayed["replayed"] is True
    metadata = replayed["item"]["payload"].get("dlq_replay", {})

    assert metadata["reason"] == "manual_admin_retry"
    assert metadata["replayed_by"] == "rc72-admin"
    assert metadata["replay_count"] == 1
    assert metadata["last_replayed_at"] is not None


async def test_rc72_replay_dead_letter_increments_replay_count():
    service = NotificationOutboxService()
    queued = await _make_dead_letter(service)

    first = await service.replay_dead_letter(
        queued["id"],
        replay_reason="first",
        replayed_by="admin",
    )
    first_item = await service.repository.get(queued["id"])
    first_item.status = "DEAD_LETTER"
    await service.repository.update(first_item)

    second = await service.replay_dead_letter(
        queued["id"],
        replay_reason="second",
        replayed_by="admin",
    )

    assert first["item"]["payload"]["dlq_replay"]["replay_count"] == 1
    assert second["item"]["payload"]["dlq_replay"]["replay_count"] == 2
