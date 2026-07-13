from app.domains.personalized_intelligence.personalization_models import UserPreferenceProfile


class InMemoryUserPreferenceRepository:
    def __init__(self):
        self.profiles: dict[str, UserPreferenceProfile] = {}

    async def save(self, profile: UserPreferenceProfile):
        self.profiles[profile.user_id] = profile
        return profile

    async def get(self, user_id: str):
        return self.profiles.get(user_id)

    async def get_or_create(self, user_id: str):
        existing = await self.get(user_id)
        if existing is not None:
            return existing

        profile = UserPreferenceProfile(user_id=user_id)
        await self.save(profile)
        return profile


class UserPreferenceRepository(InMemoryUserPreferenceRepository):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
