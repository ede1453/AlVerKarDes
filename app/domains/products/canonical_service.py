from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.domains.products.normalization.rules import normalize_text
from app.domains.products.normalization.schemas import ProductIdentity, ProductNormalizationInput
from app.domains.products.normalization.service import ProductNormalizationService


@dataclass
class CanonicalProductMatch:
    canonical_key: str
    identity: ProductIdentity
    confidence: float
    match_basis: list[str]


class CanonicalProductService:
    def __init__(self):
        self.normalizer = ProductNormalizationService()

    def build_match(self, product_name: str, country: str = "DE") -> CanonicalProductMatch:
        identity = self.normalizer.normalize(
            ProductNormalizationInput(product_name=product_name, country=country)
        )

        basis = []
        if identity.brand:
            basis.append("brand")
        if identity.product_family:
            basis.append("product_family")
        if identity.model:
            basis.append("model")
        if identity.variant.memory:
            basis.append("memory")
        if identity.variant.storage:
            basis.append("storage")

        return CanonicalProductMatch(
            canonical_key=identity.canonical_key or "",
            identity=identity,
            confidence=identity.confidence,
            match_basis=basis,
        )

    def canonicalize(self, payload: dict, country: str = "DE") -> dict:
        """CONNECT-003 (ADR-007 Karar 2): batch offer-canonicalization API,
        added so callers that previously used the standalone
        product_canonicalization domain (now archived to _arsiv/ --
        shopping_pipeline) can group offers using the SAME real identity
        engine (ProductNormalizationService) that the actual ingestion path
        uses, instead of a separate rule set with its own brand list and
        canonical_key format that could silently disagree with it (this is
        exactly the mismatch CONNECT-001 found and had to work around --
        see ADR-007 Karar 2/3). Groups offers by their real canonical_key."""
        query = payload["query"]
        offers = payload.get("offers", [])

        groups_by_key: dict[str, list[dict]] = {}
        identity_by_key: dict[str, ProductIdentity] = {}

        for offer in offers:
            product_name = offer["product_name"]
            identity = self.normalizer.normalize(
                ProductNormalizationInput(product_name=product_name, country=country)
            )
            key = identity.canonical_key or normalize_text(product_name)

            groups_by_key.setdefault(key, []).append(offer)
            identity_by_key[key] = identity

        products = []
        for key, grouped_offers in groups_by_key.items():
            identity = identity_by_key[key]
            canonical_name = sorted(
                [offer["product_name"] for offer in grouped_offers],
                key=lambda value: (len(value), value),
            )[0]
            variant = "-".join(
                part for part in [identity.variant.memory, identity.variant.storage] if part
            ) or None

            products.append(
                {
                    "canonical_id": str(uuid4()),
                    "canonical_key": key,
                    "product_name": canonical_name,
                    "brand": identity.brand,
                    "model": identity.model,
                    "variant": variant,
                    "category": identity.category_hint,
                    "confidence": round(identity.confidence),
                    "source_offer_ids": [
                        offer.get("id") or offer.get("offer_id") or "" for offer in grouped_offers
                    ],
                    "attributes": {
                        "brand": identity.brand,
                        "product_family": identity.product_family,
                        "model": identity.model,
                        "memory": identity.variant.memory,
                        "storage": identity.variant.storage,
                        "category_hint": identity.category_hint,
                    },
                    "metadata": {"canonicalization_version": "products_canonicalization_real_v1"},
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        products = sorted(products, key=lambda item: (-item["confidence"], item["canonical_key"]))

        return {
            "query": query,
            "canonical_count": len(products),
            "products": products,
            "metadata": {"canonicalization_version": "products_canonicalization_real_v1"},
        }

    def same_product(self, left_name: str, right_name: str, country: str = "DE") -> bool:
        left = self.build_match(left_name, country)
        right = self.build_match(right_name, country)

        if not left.canonical_key or not right.canonical_key:
            return False

        return left.canonical_key == right.canonical_key
