from datetime import datetime, timezone

from app.domains.user_profiles.user_profile_models import UserProfile


class InMemoryUserProfileRepository:
    def __init__(self):
        self._profiles: dict[str, UserProfile] = {}

    def upsert(self, profile: UserProfile):
        profile.updated_at = datetime.now(timezone.utc)
        self._profiles[profile.user_id] = profile
        return profile

    def get(self, user_id: str):
        return self._profiles.get(user_id)

    def get_or_create(self, user_id: str):
        profile = self._profiles.get(user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)
            self._profiles[user_id] = profile
        return profile

    def clear(self):
        self._profiles.clear()
