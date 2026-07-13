from dataclasses import dataclass, field

from app.domains.products.intelligence.product_identifier_resolver import ProductIdentifierResolver
from app.domains.products.intelligence.product_match_scorer import ProductMatchScorer
from app.domains.products.intelligence.product_signature import ProductSignatureBuilder


@dataclass
class ResolvedProductGroup:
    signature: str
    master_title: str
    offers: list
    confidence_scores: list[int] = field(default_factory=list)

    @property
    def offer_count(self) -> int:
        return len(self.offers)

    @property
    def average_confidence(self) -> float:
        if not self.confidence_scores:
            return 100.0
        return round(sum(self.confidence_scores) / len(self.confidence_scores), 2)


class CrossStoreProductResolver:
    def __init__(self, match_threshold: int = 90):
        self.signature_builder = ProductSignatureBuilder()
        self.scorer = ProductMatchScorer()
        self.match_threshold = match_threshold
        self.identifier_resolver = ProductIdentifierResolver()

    def resolve(self, offers: list, country: str = "DE") -> list[ResolvedProductGroup]:
        groups: list[ResolvedProductGroup] = []

        for offer in offers:
            title = self._title_of(offer)
            signature = self.signature_builder.build(title, country=country)

            matched_group = self._find_matching_group(groups, offer, signature, country)

            if matched_group:
                score = self.scorer.score_titles(matched_group.master_title, title)
                matched_group.offers.append(offer)
                matched_group.confidence_scores.append(score.score)
            else:
                groups.append(
                    ResolvedProductGroup(
                        signature=signature,
                        master_title=title,
                        offers=[offer],
                        confidence_scores=[],
                    )
                )

        return groups

    def _find_matching_group(self, groups: list[ResolvedProductGroup], offer, signature: str, country: str):
        title = self._title_of(offer)

        for group in groups:
            if group.signature == signature:
                return group

            for existing_offer in group.offers:
                if self.identifier_resolver.keys_match(existing_offer, offer):
                    return group

            score = self.scorer.score_titles(group.master_title, title)
            if score.score >= self.match_threshold and score.decision == "MATCH":
                return group

        return None

    def _title_of(self, offer) -> str:
        if isinstance(offer, dict):
            return offer.get("title", "")
        return getattr(offer, "title", "")
