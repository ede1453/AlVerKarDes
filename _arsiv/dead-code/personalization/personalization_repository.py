from app.domains.personalization.personalization_models import UserPreferenceProfile


class InMemoryPersonalizationRepository:
    def __init__(self):
        self._profiles: dict[str, UserPreferenceProfile] = {}

    def upsert(self, profile: UserPreferenceProfile) -> UserPreferenceProfile:
        self._profiles[profile.user_id] = profile
        return profile

    def get(self, user_id: str):
        return self._profiles.get(user_id)

    def clear(self):
        self._profiles.clear()
