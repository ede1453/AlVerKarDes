from app.domains.trust_intelligence.trust_models import TrustProfile, TrustSignal


class InMemoryTrustRepository:
    def __init__(self):
        self.signals: dict[tuple[str, str], TrustSignal] = {}
        self.profiles: dict[tuple[str, str], TrustProfile] = {}

    async def save_signal(self, signal: TrustSignal):
        self.signals[(signal.source_type, signal.source_id)] = signal
        return signal

    async def get_signal(self, source_type: str, source_id: str):
        return self.signals.get((source_type, source_id))

    async def get_or_create_signal(self, source_type: str, source_id: str):
        existing = await self.get_signal(source_type, source_id)
        if existing is not None:
            return existing

        signal = TrustSignal(source_type=source_type, source_id=source_id)
        await self.save_signal(signal)
        return signal

    async def save_profile(self, profile: TrustProfile):
        self.profiles[(profile.entity_type, profile.entity_id)] = profile
        return profile

    async def get_profile(self, entity_type: str, entity_id: str):
        return self.profiles.get((entity_type, entity_id))


class TrustRepository(InMemoryTrustRepository):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
