import re
from dataclasses import dataclass


@dataclass
class ProductIdentifier:
    gtin: str | None = None
    ean: str | None = None
    mpn: str | None = None
    sku: str | None = None

    @property
    def strongest_key(self) -> str | None:
        if self.gtin:
            return f"gtin:{self.gtin}"
        if self.ean:
            return f"ean:{self.ean}"
        if self.mpn:
            return f"mpn:{self.mpn}"
        if self.sku:
            return f"sku:{self.sku}"
        return None


class ProductIdentifierResolver:
    def resolve(self, offer) -> ProductIdentifier:
        gtin = self._clean_identifier(self._get(offer, "gtin"))
        ean = self._clean_identifier(self._get(offer, "ean"))
        mpn = self._normalize_mpn(self._get(offer, "mpn") or self._get(offer, "manufacturer_sku"))
        sku = self._normalize_sku(self._get(offer, "sku") or self._get(offer, "store_sku"))

        if gtin and not self._is_valid_gtin(gtin):
            gtin = None

        if ean and not self._is_valid_gtin(ean):
            ean = None

        return ProductIdentifier(
            gtin=gtin,
            ean=ean,
            mpn=mpn,
            sku=sku,
        )

    def keys_match(self, left_offer, right_offer) -> bool:
        left = self.resolve(left_offer)
        right = self.resolve(right_offer)

        for attr in ["gtin", "ean", "mpn"]:
            left_value = getattr(left, attr)
            right_value = getattr(right, attr)
            if left_value and right_value and left_value == right_value:
                return True

        return False

    def _get(self, offer, key: str):
        if isinstance(offer, dict):
            return offer.get(key)
        return getattr(offer, key, None)

    def _clean_identifier(self, value) -> str | None:
        if not value:
            return None
        cleaned = re.sub(r"\D", "", str(value))
        return cleaned or None

    def _normalize_mpn(self, value) -> str | None:
        if not value:
            return None
        cleaned = str(value).lower().strip()
        cleaned = re.sub(r"[^a-z0-9]", "", cleaned)
        return cleaned or None

    def _normalize_sku(self, value) -> str | None:
        if not value:
            return None
        cleaned = str(value).lower().strip()
        cleaned = re.sub(r"\s+", "-", cleaned)
        return cleaned or None

    def _is_valid_gtin(self, value: str) -> bool:
        return len(value) in {8, 12, 13, 14}
