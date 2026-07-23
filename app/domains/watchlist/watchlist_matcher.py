from __future__ import annotations

from typing import Any


class WatchlistMatcher:
    def match(
        self,
        *,
        watch_items: list[dict[str, Any]],
        opportunity: dict[str, Any],
        recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        matches = []

        product_key = opportunity.get(
            "canonical_product_key"
        )
        effective_price = float(
            opportunity.get(
                "effective_price",
                opportunity.get(
                    "price",
                    0,
                ),
            )
        )
        confidence = float(
            recommendation.get(
                "confidence",
                0,
            )
        )

        for item in watch_items:
            if not item.get(
                "active",
                True,
            ):
                continue

            if item["product_key"] != product_key:
                continue

            target_price = item.get(
                "target_price"
            )

            if (
                target_price is not None
                and effective_price
                > float(target_price)
            ):
                continue

            if confidence < float(
                item.get(
                    "minimum_confidence",
                    0,
                )
            ):
                continue

            matches.append(
                {
                    "watch_id": item["watch_id"],
                    "user_id": item["user_id"],
                    "product_key": product_key,
                    "effective_price": effective_price,
                    "confidence": confidence,
                }
            )

        return {
            "match_count": len(matches),
            "matches": matches,
            "metadata": {
                "matcher_version": "watchlist_matcher_v1"
            },
        }
