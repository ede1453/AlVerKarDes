from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from uuid import uuid4

from app.domains.products.normalization.rules import normalize_text
from app.domains.products.normalization.schemas import ProductIdentity, ProductNormalizationInput
from app.domains.products.normalization.service import ProductNormalizationService


@dataclass
class ProductMatchResult:
    left_name: str
    right_name: str
    left_identity: ProductIdentity
    right_identity: ProductIdentity
    token_score: float
    attribute_score: float
    canonical_score: float
    final_score: float
    confidence_level: str
    same_product: bool
    reasons: list[str]


class ProductMatchEngine:
    def __init__(self):
        self.normalizer = ProductNormalizationService()

    def compare(self, left_name: str, right_name: str, country: str = "DE") -> ProductMatchResult:
        left_expanded = self._expand_aliases(left_name)
        right_expanded = self._expand_aliases(right_name)

        left = self.normalizer.normalize(ProductNormalizationInput(product_name=left_expanded, country=country))
        right = self.normalizer.normalize(ProductNormalizationInput(product_name=right_expanded, country=country))

        token_score = self._token_score(left_name, right_name)
        attribute_score, reasons = self._attribute_score(left, right)
        canonical_score = self._canonical_score(left, right)

        final_score = round(
            token_score * 0.25 +
            attribute_score * 0.55 +
            canonical_score * 0.20,
            2,
        )
        
        if self._has_strong_core_match(left, right):
            final_score = max(final_score, 86.0)

        if self._has_strong_core_match(left, right) and (
            left.variant.storage == right.variant.storage or not left.variant.storage or not right.variant.storage
        ):
            final_score = max(final_score, 88.0)

        confidence_level = self._confidence_level(final_score)
        same_product = final_score >= 82 or self._has_strong_core_match(left, right)

        return ProductMatchResult(
            left_name=left_name,
            right_name=right_name,
            left_identity=left,
            right_identity=right,
            token_score=round(token_score, 2),
            attribute_score=round(attribute_score, 2),
            canonical_score=round(canonical_score, 2),
            final_score=final_score,
            confidence_level=confidence_level,
            same_product=same_product,
            reasons=reasons,
        )

    def match(self, payload: dict, country: str = "DE") -> dict:
        """CONNECT-003 (ADR-007 Karar 2): batch offer-grouping API, added so
        callers that previously used the standalone product_matching domain
        (now archived to _arsiv/ -- ai_shopping_agent) can group offers using
        the SAME real identity engine (ProductNormalizationService) that the
        actual ingestion path uses, instead of a separate first-4-token
        heuristic that could silently disagree with it (see ADR-007 Karar 2/3
        and the CONNECT-001 incident this pattern caused for price_history).
        Groups offers by their real canonical_key -- two offers land in the
        same group iff the real engine would treat them as the same product."""
        query = payload["query"]
        offers = payload.get("offers", [])

        groups_by_key: dict[str, list[dict]] = {}
        confidences_by_key: dict[str, list[float]] = {}

        for offer in offers:
            product_name = offer["product_name"]
            normalized_name = normalize_text(product_name)
            identity = self.normalizer.normalize(
                ProductNormalizationInput(product_name=product_name, country=country)
            )
            key = identity.canonical_key or normalized_name

            candidate = {
                "offer_id": offer.get("id") or offer.get("offer_id") or str(uuid4()),
                "marketplace": offer.get("marketplace", ""),
                "product_name": product_name,
                "normalized_product_name": normalized_name,
                "price": str(offer["price"]),
                "currency": offer.get("currency", "EUR"),
                "metadata": offer.get("metadata", {}),
            }

            groups_by_key.setdefault(key, []).append(candidate)
            confidences_by_key.setdefault(key, []).append(identity.confidence)

        groups = []
        for key, candidates in groups_by_key.items():
            canonical_name = sorted(candidates, key=lambda item: (len(item["product_name"]), item["product_name"]))[0][
                "product_name"
            ]
            confidences = confidences_by_key[key]
            groups.append(
                {
                    "group_id": str(uuid4()),
                    "canonical_name": canonical_name,
                    "normalized_canonical_name": key,
                    "match_confidence": round(sum(confidences) / len(confidences)),
                    "candidates": sorted(candidates, key=lambda item: (item["price"], item["marketplace"])),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        groups = sorted(groups, key=lambda group: (-len(group["candidates"]), group["canonical_name"]))

        return {
            "query": query,
            "group_count": len(groups),
            "matched_offer_count": sum(len(group["candidates"]) for group in groups),
            "groups": groups,
            "metadata": {"matching_version": "products_matching_real_v1"},
        }

    def _token_score(self, left: str, right: str) -> float:
        left_norm = normalize_text(self._expand_aliases(left))
        right_norm = normalize_text(self._expand_aliases(right))

        left_tokens = set(left_norm.split())
        right_tokens = set(right_norm.split())

        if not left_tokens or not right_tokens:
            return 0.0

        overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
        sequence = SequenceMatcher(None, left_norm, right_norm).ratio()

        return min(100.0, (overlap * 70 + sequence * 30))

    def _attribute_score(self, left: ProductIdentity, right: ProductIdentity) -> tuple[float, list[str]]:
        score = 0.0
        possible = 0.0
        reasons: list[str] = []

        def add(name: str, left_value, right_value, weight: float):
            nonlocal score, possible
            possible += weight

            if left_value and right_value and normalize_text(str(left_value)) == normalize_text(str(right_value)):
                score += weight
                reasons.append(f"{name}_match")
            elif not left_value or not right_value:
                # Missing field is not as bad as contradiction.
                score += weight * 0.35
                reasons.append(f"{name}_missing")
            else:
                reasons.append(f"{name}_mismatch")

        add("brand", left.brand, right.brand, 25)
        add("family", left.product_family, right.product_family, 25)
        add("model", left.model, right.model, 20)
        add("memory", left.variant.memory, right.variant.memory, 12.5)
        add("storage", left.variant.storage, right.variant.storage, 12.5)
        add("category", left.category_hint, right.category_hint, 5)

        if possible == 0:
            return 0.0, reasons

        return (score / possible) * 100, reasons

    def _canonical_score(self, left: ProductIdentity, right: ProductIdentity) -> float:
        if left.canonical_key and right.canonical_key and left.canonical_key == right.canonical_key:
            return 100.0

        left_parts = set((left.canonical_key or "").split("::"))
        right_parts = set((right.canonical_key or "").split("::"))

        if not left_parts or not right_parts:
            return 0.0

        return (len(left_parts & right_parts) / len(left_parts | right_parts)) * 100

    def _confidence_level(self, score: float) -> str:
        if score >= 90:
            return "HIGH"
        if score >= 75:
            return "MEDIUM"
        return "LOW"
        
    def _has_strong_core_match(self, left: ProductIdentity, right: ProductIdentity) -> bool:
        same_family = (
            left.product_family
            and right.product_family
            and normalize_text(left.product_family) == normalize_text(right.product_family)
        )
        same_model = (
            left.model
            and right.model
            and normalize_text(left.model) == normalize_text(right.model)
        )
        return bool(same_family and same_model)

    def _expand_aliases(self, value: str) -> str:
        normalized = normalize_text(value)
        replacements = {
            " mba ": " macbook air ",
            " mbp ": " macbook pro ",
            " 16/512 ": " 16gb 512gb ",
            " 8/256 ": " 8gb 256gb ",
            " 12/512 ": " 12gb 512gb ",
            " 32/1tb ": " 32gb 1tb ",
        }

        padded = f" {normalized} "
        for source, target in replacements.items():
            padded = padded.replace(source, target)

        return padded.strip()
