from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


async def test_rc71_item_moves_to_dead_letter_after_max_retries():
    service = NotificationOutboxService()
    queued = await service.enqueue(
        {
            "user_id": "rc71-user",
            "title": "RC71",
            "message": "Dead letter transition",
            "payload": {"source": "rc71"},
        }
    )

    for _ in range(3):
        await service.claim_next(worker_id="worker-rc71")
        result = await service.mark_failed(
            item_id=queued["id"],
            error="PROVIDER_TIMEOUT",
            next_retry_at="2000-01-01T00:00:00+00:00",
        )

        if result["item"]["status"] != "DEAD_LETTER":
            await service.requeue_due_retries()

    assert result["item"]["status"] == "DEAD_LETTER"
    assert result["item"]["retry_count"] == 3
    assert result["item"]["next_retry_at"] is None


async def test_rc71_list_dead_letters_returns_only_dead_letter_items():
    service = NotificationOutboxService()
    queued = await service.enqueue(
        {
            "user_id": "rc71-user",
            "title": "RC71",
            "message": "Dead letter list",
            "payload": {"source": "rc71"},
        }
    )
    await service.enqueue(
        {
            "user_id": "rc71-user",
            "title": "RC71 pending",
            "message": "Pending item",
            "payload": {"source": "rc71"},
        }
    )

    for _ in range(3):
        await service.claim_next(worker_id="worker-rc71")
        result = await service.mark_failed(
            item_id=queued["id"],
            error="PROVIDER_TIMEOUT",
            next_retry_at="2000-01-01T00:00:00+00:00",
        )

        if result["item"]["status"] != "DEAD_LETTER":
            await service.requeue_due_retries()

    dead_letters = await service.list_dead_letters()

    assert dead_letters["dead_letter_count"] == 1
    assert dead_letters["items"][0]["id"] == queued["id"]
    assert dead_letters["items"][0]["status"] == "DEAD_LETTER"


async def test_rc71_replay_dead_letter_moves_item_back_to_pending():
    service = NotificationOutboxService()
    queued = await service.enqueue(
        {
            "user_id": "rc71-user",
            "title": "RC71",
            "message": "Replay",
            "payload": {"source": "rc71"},
        }
    )

    for _ in range(3):
        await service.claim_next(worker_id="worker-rc71")
        result = await service.mark_failed(
            item_id=queued["id"],
            error="PROVIDER_TIMEOUT",
            next_retry_at="2000-01-01T00:00:00+00:00",
        )

        if result["item"]["status"] != "DEAD_LETTER":
            await service.requeue_due_retries()

    replayed = await service.replay_dead_letter(queued["id"])

    assert replayed["replayed"] is True
    assert replayed["item"]["status"] == "PENDING"
    assert replayed["item"]["last_error"] is None
    assert replayed["item"]["next_retry_at"] is None


async def test_rc71_replay_missing_dead_letter_returns_not_found():
    service = NotificationOutboxService()

    result = await service.replay_dead_letter("missing-id")

    assert result["replayed"] is False
    assert result["error"] == "NOT_FOUND"
