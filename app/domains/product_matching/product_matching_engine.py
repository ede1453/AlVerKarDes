from app.domains.product_matching.product_matching_models import (
    ProductMatchCandidate,
    ProductMatchGroup,
    ProductMatchingResult,
    create_group_id,
    normalize_product_name,
    now_utc,
)


class ProductMatchingEngine:
    def match(self, *, query: str, offers: list[dict]) -> ProductMatchingResult:
        groups_by_key: dict[str, list[ProductMatchCandidate]] = {}

        for offer in offers:
            product_name = offer["product_name"]
            normalized_name = normalize_product_name(product_name)
            key = self._group_key(normalized_name)

            candidate = ProductMatchCandidate(
                offer_id=offer.get("id") or offer.get("offer_id") or create_group_id(),
                marketplace=offer["marketplace"],
                product_name=product_name,
                normalized_product_name=normalized_name,
                price=str(offer["price"]),
                currency=offer.get("currency", "EUR"),
                metadata=offer.get("metadata", {}),
            )

            groups_by_key.setdefault(key, []).append(candidate)

        groups = [
            ProductMatchGroup(
                group_id=create_group_id(),
                canonical_name=self._canonical_name(candidates),
                normalized_canonical_name=key,
                match_confidence=self._confidence(candidates),
                candidates=sorted(candidates, key=lambda item: (item.price, item.marketplace)),
                created_at=now_utc(),
            )
            for key, candidates in groups_by_key.items()
        ]

        groups = sorted(groups, key=lambda group: (-len(group.candidates), group.canonical_name))

        return ProductMatchingResult(
            query=query,
            group_count=len(groups),
            matched_offer_count=sum(len(group.candidates) for group in groups),
            groups=groups,
            metadata={"matching_version": "product_matching_v1"},
        )

    def _group_key(self, normalized_name: str) -> str:
        tokens = normalized_name.split()
        return " ".join(tokens[:4]) if tokens else normalized_name

    def _canonical_name(self, candidates: list[ProductMatchCandidate]) -> str:
        return sorted(candidates, key=lambda item: (len(item.product_name), item.product_name))[0].product_name

    def _confidence(self, candidates: list[ProductMatchCandidate]) -> int:
        if len(candidates) >= 3:
            return 95
        if len(candidates) == 2:
            return 88
        return 70
