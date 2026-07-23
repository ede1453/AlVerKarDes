from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.user_profiles.db_models import UserProfileModel
from app.domains.user_profiles.user_profile_models import UserProfile


class InMemoryUserProfileRepository:
    """Plain in-memory test double (async methods for interface parity with
    UserProfileDBRepository -- same pattern as InMemoryJobRepository,
    SCALE-003). Not used by the real router anymore (SCALE-008); kept for
    unit tests that want a repository without a real database.
    get_or_create_for_update() here provides no real locking (a plain dict
    has no cross-process visibility or row locks) -- it exists only so
    UserProfileService's default construction still has a working
    read-modify-write path for single-process tests."""

    def __init__(self):
        self._profiles: dict[str, UserProfile] = {}

    async def upsert(self, profile: UserProfile):
        profile.updated_at = datetime.now(timezone.utc)
        self._profiles[profile.user_id] = profile
        return profile

    async def get(self, user_id: str):
        return self._profiles.get(user_id)

    async def get_or_create(self, user_id: str):
        profile = self._profiles.get(user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)
            self._profiles[user_id] = profile
        return profile

    async def get_or_create_for_update(self, user_id: str):
        return await self.get_or_create(user_id)

    async def clear(self):
        self._profiles.clear()


def _to_profile(row: UserProfileModel) -> UserProfile:
    return UserProfile(
        user_id=row.user_id,
        preferred_product_keys=list(row.preferred_product_keys or []),
        avoided_product_keys=list(row.avoided_product_keys or []),
        preferred_marketplaces=list(row.preferred_marketplaces or []),
        blocked_marketplaces=list(row.blocked_marketplaces or []),
        preferred_brands=list(row.preferred_brands or []),
        risk_tolerance=row.risk_tolerance,
        profile_score=row.profile_score,
        metadata=dict(row.metadata_json or {}),
        updated_at=row.updated_at,
    )


class UserProfileDBRepository:
    """Postgres-backed repository (SCALE-008).

    Before this, UserProfileService only ever wrote to an in-memory dict
    (InMemoryUserProfileRepository) -- worker-process-local, so a
    preference saved by one worker was invisible to another worker's
    profile_aware_recommendations read. Worse: even after moving to a real
    shared DB, a plain get()-then-upsert() sequence would still lose
    updates under concurrency (two requests reading the same starting row,
    each computing their own merge, last write wins) -- get_or_create_for_
    update() uses SELECT ... FOR UPDATE to close that gap: it locks the row
    for the rest of the caller's transaction, so a concurrent request for
    the SAME user_id blocks on its OWN SELECT FOR UPDATE until the first
    transaction commits (see upsert()), and then reads the already-merged
    result instead of a stale snapshot."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: str) -> UserProfile | None:
        row = await self.db.get(UserProfileModel, user_id)
        if row is None:
            return None
        return _to_profile(row)

    async def get_or_create(self, user_id: str) -> UserProfile:
        existing = await self.get(user_id)
        if existing is not None:
            return existing
        return await self._create_default(user_id)

    async def get_or_create_for_update(self, user_id: str) -> UserProfile:
        stmt = (
            select(UserProfileModel)
            .where(UserProfileModel.user_id == user_id)
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()

        if row is not None:
            return _to_profile(row)

        return await self._create_default(user_id, lock=True)

    async def _create_default(self, user_id: str, lock: bool = False) -> UserProfile:
        insert_stmt = (
            pg_insert(UserProfileModel)
            .values(
                user_id=user_id,
                preferred_product_keys=[],
                avoided_product_keys=[],
                preferred_marketplaces=[],
                blocked_marketplaces=[],
                preferred_brands=[],
                risk_tolerance="MEDIUM",
                profile_score=0,
                metadata_json={},
                updated_at=datetime.now(timezone.utc),
            )
            .on_conflict_do_nothing(index_elements=["user_id"])
        )
        await self.db.execute(insert_stmt)
        await self.db.commit()

        select_stmt = select(UserProfileModel).where(UserProfileModel.user_id == user_id)
        if lock:
            select_stmt = select_stmt.with_for_update()

        result = await self.db.execute(select_stmt)
        row = result.scalar_one()
        return _to_profile(row)

    async def upsert(self, profile: UserProfile) -> UserProfile:
        row = await self.db.get(UserProfileModel, profile.user_id)
        if row is None:
            row = UserProfileModel(user_id=profile.user_id)
            self.db.add(row)

        row.preferred_product_keys = list(profile.preferred_product_keys)
        row.avoided_product_keys = list(profile.avoided_product_keys)
        row.preferred_marketplaces = list(profile.preferred_marketplaces)
        row.blocked_marketplaces = list(profile.blocked_marketplaces)
        row.preferred_brands = list(profile.preferred_brands)
        row.risk_tolerance = profile.risk_tolerance
        row.profile_score = profile.profile_score
        row.metadata_json = dict(profile.metadata)
        row.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(row)
        return _to_profile(row)

    async def clear(self):
        result = await self.db.execute(select(UserProfileModel))
        for row in result.scalars().all():
            await self.db.delete(row)
        await self.db.commit()
