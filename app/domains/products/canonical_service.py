from dataclasses import dataclass

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

    def same_product(self, left_name: str, right_name: str, country: str = "DE") -> bool:
        left = self.build_match(left_name, country)
        right = self.build_match(right_name, country)

        if not left.canonical_key or not right.canonical_key:
            return False

        return left.canonical_key == right.canonical_key
