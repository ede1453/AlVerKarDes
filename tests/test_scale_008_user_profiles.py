import asyncio
import uuid

import pytest

from app.core.database import AsyncSessionLocal
from app.domains.user_profiles.user_profile_repository import UserProfileDBRepository
from app.domains.user_profiles.user_profile_service import UserProfileService


async def _apply_preferences(user_id: str, preferred_marketplaces: list[str]):
    async with AsyncSessionLocal() as db:
        service = UserProfileService(repository=UserProfileDBRepository(db))
        return await service.apply_preferences(
            {"user_id": user_id, "preferred_marketplaces": preferred_marketplaces}
        )


async def _merge_feedback(user_id: str, preferred_product_keys: list[str]):
    async with AsyncSessionLocal() as db:
        service = UserProfileService(repository=UserProfileDBRepository(db))
        return await service.merge_feedback(
            {
                "user_id": user_id,
                "feedback_summary": {
                    "event_count": 1,
                    "preferred_product_keys": preferred_product_keys,
                },
            }
        )


async def test_scale_008_db_repository_get_or_create_and_upsert():
    user_id = f"scale008-basic-{uuid.uuid4().hex}"

    async with AsyncSessionLocal() as db:
        repository = UserProfileDBRepository(db)

        created = await repository.get_or_create(user_id)
        assert created.user_id == user_id
        assert created.preferred_marketplaces == []

        created.preferred_marketplaces = ["saturn"]
        saved = await repository.upsert(created)
        assert saved.preferred_marketplaces == ["saturn"]

    async with AsyncSessionLocal() as db:
        repository = UserProfileDBRepository(db)
        fetched = await repository.get(user_id)
        assert fetched.preferred_marketplaces == ["saturn"]


async def test_scale_008_two_workers_updating_same_user_neither_update_is_lost():
    # SCALE-008: two REAL, separate AsyncSession connections (simulating
    # two separate worker processes, each with its own DB connection)
    # concurrently update DIFFERENT fields of the SAME user's profile.
    # get_or_create_for_update()'s SELECT ... FOR UPDATE means the second
    # writer's read blocks on real Postgres row-locking until the first
    # writer's transaction commits, so it always merges on top of the
    # already-written result instead of a stale snapshot -- a plain
    # get()-then-upsert() would let one of these two updates silently
    # overwrite the other (last write wins).
    user_id = f"scale008-concurrent-{uuid.uuid4().hex}"

    await asyncio.gather(
        _apply_preferences(user_id, ["saturn"]),
        _merge_feedback(user_id, ["macbook-air"]),
    )

    async with AsyncSessionLocal() as db:
        service = UserProfileService(repository=UserProfileDBRepository(db))
        context = await service.recommendation_context(user_id)

    assert context["preferred_marketplaces"] == ["saturn"], "apply_preferences' update was lost"
    assert context["preferred_product_keys"] == ["macbook-air"], "merge_feedback's update was lost"


async def test_scale_008_profile_persists_across_separate_sessions():
    user_id = f"scale008-persist-{uuid.uuid4().hex}"

    await _apply_preferences(user_id, ["saturn", "amazon"])

    async with AsyncSessionLocal() as db:
        service = UserProfileService(repository=UserProfileDBRepository(db))
        profile = await service.get_profile(user_id)

    assert profile["preferred_marketplaces"] == ["saturn", "amazon"]
