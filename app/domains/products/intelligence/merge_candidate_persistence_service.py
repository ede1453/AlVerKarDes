from app.domains.products.intelligence.cross_store_resolver import CrossStoreProductResolver
from app.domains.products.intelligence.merge_candidate_engine import MergeCandidateEngine
from app.domains.products.intelligence.merge_candidate_repository import MergeCandidateRepository


class MergeCandidatePersistenceService:
    def __init__(self, db):
        self.resolver = CrossStoreProductResolver()
        self.engine = MergeCandidateEngine()
        self.repository = MergeCandidateRepository(db)

    async def build_and_persist(self, *, offers: list, country: str = "DE"):
        groups = self.resolver.resolve(offers, country=country)
        candidates = self.engine.build_candidates(groups)

        saved = []
        for candidate in candidates:
            saved.append(await self.repository.create_from_candidate(candidate))

        return {
            "country": country,
            "input_offer_count": len(offers),
            "candidate_count": len(candidates),
            "saved_count": len(saved),
            "saved_ids": [str(item.id) for item in saved],
        }
