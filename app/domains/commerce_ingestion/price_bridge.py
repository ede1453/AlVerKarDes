from __future__ import annotations

from copy import deepcopy
from typing import Any


class PriceHistoryBridge:
    def __init__(self) -> None:
        self._history: dict[str, list[dict[str, Any]]] = {}

    def append_snapshot(
        self,
        *,
        canonical_product_key: str,
        source_id: str,
        external_offer_id: str,
        price: float,
        currency: str,
        observed_at: str,
        snapshot_id: str,
    ) -> dict[str, Any]:
        item = {
            "canonical_product_key": canonical_product_key,
            "source_id": source_id,
            "external_offer_id": external_offer_id,
            "price": float(price),
            "currency": currency.upper(),
            "observed_at": observed_at,
            "snapshot_id": snapshot_id,
        }

        self._history.setdefault(
            canonical_product_key,
            [],
        ).append(item)

        self._history[canonical_product_key].sort(
            key=lambda value: value["observed_at"]
        )

        return deepcopy(item)

    def get_history(
        self,
        canonical_product_key: str,
    ) -> dict[str, Any]:
        items = self._history.get(
            canonical_product_key,
            [],
        )

        return {
            "canonical_product_key": canonical_product_key,
            "price_point_count": len(items),
            "price_points": deepcopy(items),
            "latest_price": (
                items[-1]["price"]
                if items
                else None
            ),
            "lowest_price": (
                min(item["price"] for item in items)
                if items
                else None
            ),
            "highest_price": (
                max(item["price"] for item in items)
                if items
                else None
            ),
            "metadata": {
                "bridge_version": "price_history_bridge_v1"
            },
        }
