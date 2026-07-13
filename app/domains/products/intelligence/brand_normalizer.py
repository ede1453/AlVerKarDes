import re


class BrandNormalizer:
    KNOWN_ALIASES = {
        " apple": "apple",
        "apple inc": "apple",
        "apple inc.": "apple",
        "apple computer": "apple",
        "samsung electronics": "samsung",
        "hewlett packard": "hp",
        "hp inc": "hp",
        "lenovo group": "lenovo",
    }

    def normalize(self, value: str | None) -> str | None:
        if not value:
            return None

        cleaned = value.lower().strip()
        cleaned = cleaned.replace("®", "").replace("™", "")
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = cleaned.strip(" .,-_/")

        return self.KNOWN_ALIASES.get(cleaned, cleaned)
