import pytest

from app.domains.personalized_intelligence.personalization_models import UserPreferenceProfile
from app.domains.personalized_intelligence.user_preference_repository import (
    InMemoryUserPreferenceRepository,
)


@pytest.mark.asyncio
async def test_user_preference_repository_saves_and_reads_profile():
    repo = InMemoryUserPreferenceRepository()

    await repo.save(
        UserPreferenceProfile(
            user_id="user-1",
            preferred_brands=["apple"],
        )
    )

    found = await repo.get("user-1")

    assert found.user_id == "user-1"
    assert found.preferred_brands == ["apple"]


@pytest.mark.asyncio
async def test_user_preference_repository_get_or_create():
    repo = InMemoryUserPreferenceRepository()

    profile = await repo.get_or_create("user-1")

    assert profile.user_id == "user-1"
    assert profile.price_sensitivity == "MEDIUM"
