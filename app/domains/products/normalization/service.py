import re

from app.domains.products.normalization.rules import (
    build_canonical_key,
    detect_brand,
    detect_category,
    detect_memory,
    detect_storage,
    normalize_text,
)
from app.domains.products.normalization.schemas import ProductIdentity, ProductNormalizationInput, VariantAttributes


class ProductNormalizationService:
    def normalize(self, payload: ProductNormalizationInput) -> ProductIdentity:
        source = payload.product_name or payload.raw_title or str(payload.product_url or "")
        normalized = normalize_text(source)

        brand = detect_brand(source)
        category = detect_category(source)
        memory = detect_memory(source)
        storage = detect_storage(source)
        family = self._detect_family(normalized)
        model = self._detect_model(normalized)

        missing = [
            key
            for key, value in {
                "brand": brand,
                "product_family": family,
                "model": model,
            }.items()
            if not value
        ]

        score = self._score_identity(
            brand=brand,
            family=family,
            model=model,
            category=category,
            memory=memory,
            storage=storage,
        )

        canonical_key = build_canonical_key(
            [brand, family, model, memory, storage], payload.country, source
        )

        return ProductIdentity(
            brand=brand,
            product_family=family,
            model=model,
            category_hint=category,
            variant=VariantAttributes(memory=memory, storage=storage),
            canonical_key=canonical_key,
            confidence=score,
            missing_fields=missing,
            raw_input=payload.model_dump(mode="json"),
        )

    def _score_identity(
        self,
        *,
        brand: str | None,
        family: str | None,
        model: str | None,
        category: str | None,
        memory: str | None,
        storage: str | None,
    ) -> float:
        score = 0.0
        score += 25 if brand else 0
        score += 25 if family else 0
        score += 20 if model else 0
        score += 10 if category else 0
        score += 10 if memory else 0
        score += 10 if storage else 0
        return min(score, 100.0)

    def _detect_family(self, text: str) -> str | None:
        families = [
            "macbook air",
            "macbook pro",
            "iphone",
            "ipad pro",
            "ipad air",
            "galaxy s",
            "galaxy z",
            "thinkpad",
            "xps",
            "airpods pro",
            "wh-1000xm",
        ]

        for family in families:
            if family in text:
                if family == "wh-1000xm":
                    return "WH-1000XM"
                return family.title()

        return None

    def _detect_model(self, text: str) -> str | None:
        match = re.search(r"\b(m[1-9])\b", text, re.I)
        if match:
            return match.group(1).upper()

        match = re.search(r"\b(wh-?1000xm\d)\b", text, re.I)
        if match:
            value = match.group(1).upper()
            return value.replace("WH1000", "WH-1000")

        match = re.search(r"\b(s\d{2})\b", text, re.I)
        if match:
            return match.group(1).upper()

        match = re.search(r"\b([a-z]{1,4}\d{2,5}[a-z0-9\-]*)\b", text, re.I)
        return match.group(1).upper() if match else None
