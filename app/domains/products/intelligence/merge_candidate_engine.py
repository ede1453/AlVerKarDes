from dataclasses import dataclass, field


@dataclass
class MergeCandidate:
    signature: str
    master_title: str
    offer_count: int
    average_confidence: float
    decision: str
    offer_titles: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


class MergeCandidateEngine:
    def __init__(self, auto_merge_threshold: float = 90.0, review_threshold: float = 70.0):
        self.auto_merge_threshold = auto_merge_threshold
        self.review_threshold = review_threshold

    def build_candidates(self, groups: list) -> list[MergeCandidate]:
        candidates = []

        for group in groups:
            if getattr(group, "offer_count", len(group.offers)) < 2:
                continue

            confidence = float(group.average_confidence)

            if confidence >= self.auto_merge_threshold:
                decision = "AUTO_MERGE"
            elif confidence >= self.review_threshold:
                decision = "REVIEW"
            else:
                decision = "DO_NOT_MERGE"

            candidates.append(
                MergeCandidate(
                    signature=group.signature,
                    master_title=group.master_title,
                    offer_count=group.offer_count,
                    average_confidence=confidence,
                    decision=decision,
                    offer_titles=[self._title_of(offer) for offer in group.offers],
                    sources=[self._source_of(offer) for offer in group.offers if self._source_of(offer)],
                )
            )

        return candidates

    def _title_of(self, offer) -> str:
        if isinstance(offer, dict):
            return offer.get("title", "")
        return getattr(offer, "title", "")

    def _source_of(self, offer) -> str | None:
        if isinstance(offer, dict):
            return offer.get("source")
        return getattr(offer, "source", None)
