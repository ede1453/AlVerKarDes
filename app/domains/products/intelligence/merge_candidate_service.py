from app.domains.products.intelligence.cross_store_resolver import CrossStoreProductResolver
from app.domains.products.intelligence.merge_candidate_engine import MergeCandidateEngine


class MergeCandidateService:
    def __init__(self):
        self.resolver = CrossStoreProductResolver()
        self.engine = MergeCandidateEngine()

    def build_from_offers(self, *, offers: list, country: str = "DE"):
        groups = self.resolver.resolve(offers, country=country)
        candidates = self.engine.build_candidates(groups)

        return {
            "country": country,
            "input_offer_count": len(offers),
            "candidate_count": len(candidates),
            "candidates": [
                {
                    "signature": item.signature,
                    "master_title": item.master_title,
                    "offer_count": item.offer_count,
                    "average_confidence": item.average_confidence,
                    "decision": item.decision,
                    "offer_titles": item.offer_titles,
                    "sources": item.sources,
                }
                for item in candidates
            ],
        }
