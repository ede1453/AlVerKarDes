from app.domains.user_profiles.user_profile_repository import InMemoryUserProfileRepository

_default_user_profile_repository = InMemoryUserProfileRepository()


def get_user_profile_repository():
    return _default_user_profile_repository


def reset_user_profile_repository():
    _default_user_profile_repository.clear()