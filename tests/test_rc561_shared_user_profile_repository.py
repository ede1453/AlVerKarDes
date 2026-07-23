from app.domains.user_profiles.user_profile_repository_factory import (
    reset_user_profile_repository,
)
from app.domains.user_profiles.user_profile_service import UserProfileService


async def test_rc561_user_profile_service_instances_share_default_repository():
    await reset_user_profile_repository()

    writer = UserProfileService()
    reader = UserProfileService()

    await writer.apply_preferences(
        {
            "user_id": "user-1",
            "preferred_marketplaces": ["saturn"],
            "preferred_brands": ["Apple"],
            "risk_tolerance": "LOW",
        }
    )

    context = await reader.recommendation_context("user-1")

    assert context["preferred_marketplaces"] == ["saturn"]
    assert context["preferred_brands"] == ["Apple"]
    assert context["risk_tolerance"] == "LOW"


async def test_rc561_reset_user_profile_repository_clears_shared_state():
    await reset_user_profile_repository()

    service = UserProfileService()
    await service.apply_preferences(
        {
            "user_id": "user-1",
            "preferred_marketplaces": ["saturn"],
        }
    )

    assert (await service.recommendation_context("user-1"))["preferred_marketplaces"] == ["saturn"]

    await reset_user_profile_repository()

    assert (await UserProfileService().recommendation_context("user-1"))["preferred_marketplaces"] == []
