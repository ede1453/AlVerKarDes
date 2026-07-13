import re
from dataclasses import dataclass


@dataclass
class ProductSpec:
    brand: str | None = None
    model_family: str | None = None
    chip: str | None = None
    ram_gb: int | None = None
    storage_gb: int | None = None
    color: str | None = None


class ProductSpecExtractor:
    COLOR_WORDS = {
        "midnight",
        "silver",
        "space gray",
        "space grey",
        "starlight",
        "black",
        "white",
        "blue",
    }

    def extract(self, title: str) -> ProductSpec:
        text = self._normalize_text(title)

        return ProductSpec(
            brand=self._extract_brand(text),
            model_family=self._extract_model_family(text),
            chip=self._extract_chip(text),
            ram_gb=self._extract_ram(text),
            storage_gb=self._extract_storage(text),
            color=self._extract_color(text),
        )

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.lower()).strip()

    def _extract_brand(self, text: str) -> str | None:
        for brand in ["apple", "samsung", "lenovo", "hp", "dell", "asus", "acer", "sony"]:
            if re.search(rf"\b{re.escape(brand)}\b", text):
                return brand
        return None

    def _extract_model_family(self, text: str) -> str | None:
        if "macbook air" in text or re.search(r"\bmba\b", text):
            return "macbook air"
        if "macbook pro" in text or re.search(r"\bmbp\b", text):
            return "macbook pro"
        if "thinkpad x1" in text:
            return "thinkpad x1"
        if "xps" in text:
            return "xps"
        return None

    def _extract_chip(self, text: str) -> str | None:
        match = re.search(r"\b(m[1-9])\b", text)
        if match:
            return match.group(1)
        return None

    def _extract_ram(self, text: str) -> int | None:
        match = re.search(r"\b(8|16|24|32|64)\s*gb\b", text)
        if match:
            return int(match.group(1))

        compact = re.search(r"\b(8|16|24|32|64)\s*/\s*(256|512|1024|1tb|2tb)\b", text)
        if compact:
            return int(compact.group(1))

        return None

    def _extract_storage(self, text: str) -> int | None:
        compact = re.search(r"\b(8|16|24|32|64)\s*/\s*(256|512|1024|1tb|2tb)\b", text)
        if compact:
            return self._storage_to_gb(compact.group(2))

        matches = re.findall(r"\b(256|512|1024|1tb|2tb)\s*(gb|tb)?\b", text)
        if not matches:
            return None

        value, unit = matches[-1]
        return self._storage_to_gb(value if unit == "" else f"{value}{unit}")

    def _storage_to_gb(self, value: str) -> int:
        value = value.lower().replace(" ", "")

        if value.endswith("tb"):
            return int(value.replace("tb", "")) * 1024

        if value.endswith("gb"):
            return int(value.replace("gb", ""))

        return int(value)

    def _extract_color(self, text: str) -> str | None:
        for color in sorted(self.COLOR_WORDS, key=len, reverse=True):
            if color in text:
                return color.replace("grey", "gray")
        return None
