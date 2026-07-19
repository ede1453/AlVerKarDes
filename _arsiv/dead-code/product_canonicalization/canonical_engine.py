from app.domains.product_canonicalization.canonical_models import (
    CanonicalizationResult,
    CanonicalProduct,
    create_canonical_id,
)
from app.domains.product_canonicalization.canonical_rules import ProductCanonicalRules


class ProductCanonicalizationEngine:
    def __init__(self, rules: ProductCanonicalRules | None = None):
        self.rules = rules or ProductCanonicalRules()

    def canonicalize(self, *, query: str, offers: list[dict]):
        grouped: dict[str, list[dict]] = {}
        attributes_by_key: dict[str, dict] = {}

        for offer in offers:
            product_name = offer["product_name"]
            normalized = self.rules.normalize(product_name)
            brand = offer.get("brand") or self.rules.detect_brand(normalized)
            model = offer.get("model") or self.rules.detect_model(normalized)
            variant = offer.get("variant") or self.rules.detect_variant(normalized)
            category = offer.get("category") or self.rules.infer_category(normalized)
            key = self.rules.canonical_key(
                brand=brand,
                model=model,
                variant=variant,
                fallback=product_name,
            )

            grouped.setdefault(key, []).append(offer)
            attributes_by_key[key] = {
                "brand": brand,
                "model": model,
                "variant": variant,
                "category": category,
                "normalized_name": normalized,
            }

        products = []
        for key, grouped_offers in grouped.items():
            attrs = attributes_by_key[key]
            confidence = self._confidence(attrs, grouped_offers)
            canonical_name = self._canonical_name(grouped_offers)

            products.append(
                CanonicalProduct(
                    canonical_id=create_canonical_id(),
                    canonical_key=key,
                    product_name=canonical_name,
                    brand=attrs["brand"],
                    model=attrs["model"],
                    variant=attrs["variant"],
                    category=attrs["category"],
                    confidence=confidence,
                    source_offer_ids=[
                        offer.get("id") or offer.get("offer_id") or ""
                        for offer in grouped_offers
                    ],
                    attributes=attrs,
                    metadata={"canonicalization_version": "product_canonicalization_v2"},
                )
            )

        products = sorted(products, key=lambda item: (-item.confidence, item.canonical_key))

        return CanonicalizationResult(
            query=query,
            canonical_count=len(products),
            products=products,
            metadata={"canonicalization_version": "product_canonicalization_v2"},
        )

    def _canonical_name(self, offers: list[dict]):
        return sorted([offer["product_name"] for offer in offers], key=lambda value: (len(value), value))[0]

    def _confidence(self, attrs: dict, offers: list[dict]):
        confidence = 50
        if attrs.get("brand"):
            confidence += 15
        if attrs.get("model"):
            confidence += 20
        if attrs.get("variant"):
            confidence += 10
        if len(offers) >= 2:
            confidence += 5
        return max(0, min(100, confidence))
