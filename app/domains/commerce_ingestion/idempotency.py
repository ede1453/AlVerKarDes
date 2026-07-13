from __future__ import annotations

from hashlib import sha256
from typing import Any


class IngestionIdempotencyService:
    def __init__(self) -> None:
        self._keys: set[str] = set()

    def build_key(
        self,
        *,
        source_id: str,
        external_offer_id: str,
        observed_at: str,
        price: float,
        currency: str,
    ) -> str:
        raw = "|".join(
            [
                source_id,
                external_offer_id,
                observed_at,
                str(float(price)),
                currency.upper(),
            ]
        )
        return sha256(raw.encode("utf-8")).hexdigest()

    def reserve(self, key: str) -> dict[str, Any]:
        if key in self._keys:
            return {
                "reserved": False,
                "reason": "IDEMPOTENCY_KEY_EXISTS",
                "key": key,
            }

        self._keys.add(key)
        return {
            "reserved": True,
            "reason": "IDEMPOTENCY_KEY_RESERVED",
            "key": key,
        }

    def contains(self, key: str) -> bool:
        return key in self._keys
