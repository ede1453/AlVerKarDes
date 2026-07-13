import re

KNOWN_BRANDS = ["apple", "samsung", "sony", "lenovo", "asus", "hp", "dell", "xiaomi"]


class ProductCanonicalRules:
    def normalize(self, value: str) -> str:
        return " ".join(
            value.lower()
            .replace("-", " ")
            .replace("_", " ")
            .replace(",", " ")
            .split()
        )

    def detect_brand(self, normalized_name: str):
        for brand in KNOWN_BRANDS:
            if brand in normalized_name.split():
                return brand
        return None

    def detect_model(self, normalized_name: str):
        patterns = [
            r"macbook air(?: m\d)?",
            r"iphone\s?\d{1,2}(?:\s?pro)?(?:\s?max)?",
            r"galaxy\s?s\d{1,2}",
            r"thinkpad\s?[a-z]\d+",
            r"xps\s?\d+",
        ]
        for pattern in patterns:
            match = re.search(pattern, normalized_name)
            if match:
                return " ".join(match.group(0).split())
        return None

    def detect_variant(self, normalized_name: str):
        variant_parts = []

        storage = re.search(r"(\d+\s?(gb|tb))", normalized_name)
        if storage:
            variant_parts.append(storage.group(1).replace(" ", ""))

        memory = re.search(r"(\d+\s?gb)\s?ram", normalized_name)
        if memory:
            variant_parts.append(memory.group(1).replace(" ", "") + "-ram")

        screen = re.search(r"(\d{2}(?:\.\d)?\s?(inch|in|\"))", normalized_name)
        if screen:
            variant_parts.append(screen.group(1).replace(" ", ""))

        chip = re.search(r"\bm\d\b", normalized_name)
        if chip:
            variant_parts.append(chip.group(0))

        return "-".join(dict.fromkeys(variant_parts)) or None

    def infer_category(self, normalized_name: str):
        if "macbook" in normalized_name or "thinkpad" in normalized_name or "xps" in normalized_name:
            return "laptop"
        if "iphone" in normalized_name or "galaxy" in normalized_name:
            return "smartphone"
        return None

    def canonical_key(self, *, brand: str | None, model: str | None, variant: str | None, fallback: str):
        parts = [part for part in [brand, model, variant] if part]
        if parts:
            return "-".join(self.normalize(" ".join(parts)).split())
        return "-".join(self.normalize(fallback).split()[:6])
