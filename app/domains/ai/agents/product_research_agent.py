from dataclasses import dataclass

from app.domains.products.normalization.schemas import ProductIdentity, ProductNormalizationInput
from app.domains.products.normalization.service import ProductNormalizationService


@dataclass
class ProductResearchResult:
    identity: ProductIdentity
    enrichment: dict
    used_llm: bool
    confidence: float
    uncertainty: dict


class ProductResearchAgent:
    name = "ProductResearchAgent"

    def __init__(self, normalizer: ProductNormalizationService):
        self.normalizer = normalizer

    async def run(self, payload: ProductNormalizationInput) -> ProductResearchResult:
        identity = self.normalizer.normalize(payload)
        level = "LOW" if identity.confidence >= 80 else "MEDIUM" if identity.confidence >= 50 else "HIGH"
        return ProductResearchResult(
            identity=identity,
            enrichment={},
            used_llm=False,
            confidence=identity.confidence,
            uncertainty={"level": level, "explanation": "Rule-based product normalization used."},
        )
