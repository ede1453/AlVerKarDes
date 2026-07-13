from app.domains.products.intelligence.brand_normalizer import BrandNormalizer
from app.domains.products.intelligence.spec_extractor import ProductSpecExtractor


class ProductSignatureBuilder:
    def __init__(self):
        self.brand_normalizer = BrandNormalizer()
        self.extractor = ProductSpecExtractor()

    def build(self, title: str, country: str = "DE") -> str:
        spec = self.extractor.extract(title)
        brand = self.brand_normalizer.normalize(spec.brand)

        parts = [
            brand,
            spec.model_family,
            spec.chip,
            f"{spec.ram_gb}gb" if spec.ram_gb else None,
            f"{spec.storage_gb}gb" if spec.storage_gb else None,
            country.lower(),
        ]

        return "::".join([part for part in parts if part])
