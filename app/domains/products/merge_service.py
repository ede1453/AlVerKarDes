from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProductMergeCandidate:
    product_id: str
    canonical_key: str
    title: str
    confidence: float = 0.0
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductMergePlan:
    master_product_id: str
    master_canonical_key: str
    duplicate_product_ids: list[str]
    canonical_keys: list[str]
    confidence: float
    reason: str
    candidate_count: int


class ProductMergeService:
    def build_merge_plan(self, candidates: list[ProductMergeCandidate]) -> ProductMergePlan | None:
        clean = [item for item in candidates if item.product_id and item.canonical_key]

        if len(clean) < 2:
            return None

        master = self._select_master(clean)
        duplicates = [item.product_id for item in clean if item.product_id != master.product_id]
        canonical_keys = sorted({item.canonical_key for item in clean})

        if not duplicates:
            return None

        confidence = self._merge_confidence(clean, master)

        return ProductMergePlan(
            master_product_id=master.product_id,
            master_canonical_key=master.canonical_key,
            duplicate_product_ids=duplicates,
            canonical_keys=canonical_keys,
            confidence=confidence,
            reason="same_match_group",
            candidate_count=len(clean),
        )

    def _select_master(self, candidates: list[ProductMergeCandidate]) -> ProductMergeCandidate:
        def score(item: ProductMergeCandidate):
            completeness = 0
            key = item.canonical_key or ""

            # More complete canonical keys should win.
            completeness += 20 if "macbook-air" in key or "thinkpad" in key or "galaxy" in key else 0
            completeness += 10 if "16gb" in key or "32gb" in key or "12gb" in key else 0
            completeness += 10 if "512gb" in key or "1tb" in key or "256gb" in key else 0
            completeness += len(key.split("::"))

            return (
                item.confidence,
                completeness,
                len(key),
                item.title,
            )

        return sorted(candidates, key=score, reverse=True)[0]

    def _merge_confidence(self, candidates: list[ProductMergeCandidate], master: ProductMergeCandidate) -> float:
        avg_confidence = sum(item.confidence for item in candidates) / len(candidates)
        key_overlap_bonus = 10 if len({item.canonical_key for item in candidates}) > 1 else 0
        master_bonus = 10 if master.confidence >= 90 else 0
        return min(round(avg_confidence + key_overlap_bonus + master_bonus, 2), 100.0)
