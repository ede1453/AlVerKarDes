import hashlib
import re
import unicodedata

KNOWN_BRANDS = [
    "apple", "samsung", "sony", "lg", "lenovo", "asus", "acer", "dell", "hp",
    "bosch", "siemens", "dyson", "philips", "xiaomi", "anker", "logitech"
]


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.strip().lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9äöüß\s\-\.]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def detect_brand(text: str) -> str | None:
    normalized = normalize_text(text)
    for brand in KNOWN_BRANDS:
        if re.search(rf"\b{re.escape(brand)}\b", normalized):
            return brand.title()
    return None


def detect_memory(text: str) -> str | None:
    normalized = normalize_text(text)
    ram_match = re.search(
        r"\b(4|6|8|12|16|18|24|32|36|48|64|96|128)\s?gb\s?(ram|memory|unified memory)?\b",
        normalized,
        re.I,
    )

    if ram_match:
        value = ram_match.group(1)
        if any(token in normalized for token in ["macbook", "laptop", "notebook", "thinkpad", "xps"]):
            return f"{value}GB"
        if ram_match.group(2):
            return f"{value}GB"

    return None


def detect_storage(text: str) -> str | None:
    normalized = normalize_text(text)
    explicit = re.search(
        r"\b(64|128|256|512)\s?gb\s?(ssd|storage)?\b|\b(1|2|4|8)\s?tb\s?(ssd|storage)?\b",
        normalized,
        re.I,
    )
    if not explicit:
        return None

    all_gb = [int(v) for v in re.findall(r"\b(\d+)\s?gb\b", normalized)]
    if len(all_gb) >= 2:
        return f"{max(all_gb)}GB"

    if explicit.group(1):
        return f"{explicit.group(1)}GB"
    return f"{explicit.group(3)}TB"


def detect_category(text: str) -> str | None:
    normalized = normalize_text(text)
    if any(token in normalized for token in ["macbook", "thinkpad", "xps", "laptop", "notebook"]):
        return "laptop"
    if any(token in normalized for token in ["iphone", "galaxy", "pixel", "smartphone"]):
        return "smartphone"
    if "ipad" in normalized or "tablet" in normalized:
        return "tablet"
    if any(token in normalized for token in ["wh-1000", "headphone", "headphones", "earbuds"]):
        return "headphones"
    return None


def build_canonical_key(
    identity_parts: list[str | None], country: str | None, fallback_source: str
) -> str:
    """CONNECT-005: identity_parts (brand/family/model/memory/storage) are
    joined with country only when AT LEAST ONE was actually detected. When
    none were detected, country alone used to be returned as the key (e.g.
    "de") -- meaning any two products the detectors couldn't recognize at
    all would collide on the exact same canonical_key and silently dedupe
    into one products row, mixing their price history. The fallback here is
    a hash of the product's own distinguishing text (+ country) instead, so
    two different unrecognized products only collide if their source text
    (product_name/raw_title/product_url) and country are also identical --
    which is the correct dedup behavior, not a bug."""
    cleaned = [re.sub(r"\s+", "-", normalize_text(p)) for p in identity_parts if p]
    if cleaned:
        if country:
            cleaned.append(re.sub(r"\s+", "-", normalize_text(country)))
        return "::".join(cleaned)

    digest_input = f"{normalize_text(fallback_source)}::{normalize_text(country or '')}"
    digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:16]
    return f"unrecognized::{digest}"
