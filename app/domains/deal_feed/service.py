from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProductIdentityResolver:
    def resolve(
        self,
        *,
        offer: dict[str, Any],
    ) -> dict[str, Any]:
        canonical = offer.get(
            "canonical_product_key"
        )

        if canonical:
            return {
                "resolved": True,
                "product_key": str(canonical),
                "confidence": 100,
                "reason": "CANONICAL_KEY_PRESENT",
            }

        parts = [
            str(offer.get("brand") or "").strip().lower(),
            str(offer.get("product_family") or "").strip().lower(),
            str(offer.get("model") or "").strip().lower(),
            str(offer.get("memory") or "").strip().lower(),
            str(offer.get("storage") or "").strip().lower(),
        ]

        non_empty = [part for part in parts if part]

        if len(non_empty) < 2:
            return {
                "resolved": False,
                "product_key": None,
                "confidence": 0,
                "reason": "INSUFFICIENT_IDENTITY_FIELDS",
            }

        key = "::".join(
            part.replace(" ", "-")
            for part in non_empty
        )

        confidence = min(
            100,
            len(non_empty) * 20,
        )

        return {
            "resolved": True,
            "product_key": key,
            "confidence": confidence,
            "reason": "IDENTITY_FIELDS_COMBINED",
            "metadata": {
                "resolver_version": "product_identity_v1"
            },
        }


class OfferDeduplicator:
    def fingerprint(
        self,
        offer: dict[str, Any],
    ) -> str:
        raw = "|".join(
            [
                str(
                    offer.get(
                        "source_id",
                        offer.get("marketplace", ""),
                    )
                ),
                str(
                    offer.get(
                        "external_offer_id",
                        "",
                    )
                ),
                str(
                    offer.get(
                        "canonical_product_key",
                        "",
                    )
                ),
                str(float(offer.get("price", 0))),
                str(
                    offer.get(
                        "currency",
                        "",
                    )
                ).upper(),
            ]
        )

        return sha256(
            raw.encode("utf-8")
        ).hexdigest()

    def deduplicate(
        self,
        *,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        unique: list[dict[str, Any]] = []
        duplicate_items: list[dict[str, Any]] = []
        seen: dict[str, dict[str, Any]] = {}

        for offer in offers:
            fingerprint = self.fingerprint(
                offer
            )

            if fingerprint in seen:
                duplicate_items.append(
                    {
                        "fingerprint": fingerprint,
                        "duplicate": deepcopy(offer),
                        "original": deepcopy(
                            seen[fingerprint]
                        ),
                    }
                )
                continue

            stored = {
                **offer,
                "offer_fingerprint": fingerprint,
            }

            seen[fingerprint] = stored
            unique.append(stored)

        return {
            "input_count": len(offers),
            "unique_count": len(unique),
            "duplicate_count": len(
                duplicate_items
            ),
            "offers": unique,
            "duplicates": duplicate_items,
            "metadata": {
                "dedup_version": "offer_dedup_v1"
            },
        }


class UserPreferenceScorer:
    def score(
        self,
        *,
        deal: dict[str, Any],
        preferences: dict[str, Any],
    ) -> dict[str, Any]:
        base_score = float(
            deal.get(
                "opportunity_score",
                deal.get(
                    "confidence_score",
                    0,
                ),
            )
        )

        score = base_score
        reasons: list[str] = []

        preferred_categories = {
            str(value).lower()
            for value in preferences.get(
                "preferred_categories",
                [],
            )
        }

        preferred_brands = {
            str(value).lower()
            for value in preferences.get(
                "preferred_brands",
                [],
            )
        }

        blocked_sources = {
            str(value).lower()
            for value in preferences.get(
                "blocked_sources",
                [],
            )
        }

        category = str(
            deal.get("category", "")
        ).lower()

        brand = str(
            deal.get("brand", "")
        ).lower()

        source = str(
            deal.get(
                "source_id",
                deal.get("marketplace", ""),
            )
        ).lower()

        if (
            preferred_categories
            and category in preferred_categories
        ):
            score += 10
            reasons.append(
                "PREFERRED_CATEGORY"
            )

        if (
            preferred_brands
            and brand in preferred_brands
        ):
            score += 10
            reasons.append(
                "PREFERRED_BRAND"
            )

        if source in blocked_sources:
            score -= 100
            reasons.append(
                "BLOCKED_SOURCE"
            )

        maximum_price = preferences.get(
            "maximum_price"
        )

        effective_price = float(
            deal.get(
                "effective_price",
                deal.get("price", 0),
            )
        )

        if (
            maximum_price is not None
            and effective_price
            > float(maximum_price)
        ):
            score -= 30
            reasons.append(
                "ABOVE_MAXIMUM_PRICE"
            )

        minimum_discount = float(
            preferences.get(
                "minimum_discount_pct",
                0,
            )
        )

        observed_discount = float(
            deal.get(
                "observed_discount_pct",
                0,
            )
        )

        if observed_discount >= minimum_discount:
            score += 5
            reasons.append(
                "DISCOUNT_THRESHOLD_MET"
            )

        final_score = round(
            min(max(score, 0), 100),
            2,
        )

        return {
            "personalized_score": final_score,
            "base_score": round(base_score, 2),
            "reasons": reasons,
            "eligible": "BLOCKED_SOURCE" not in reasons,
            "metadata": {
                "scoring_version": "user_preference_score_v1"
            },
        }


class DealFeedBuilder:
    def build(
        self,
        *,
        deals: list[dict[str, Any]],
        preferences: dict[str, Any] | None = None,
        minimum_confidence: float = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        preferences = preferences or {}
        scorer = UserPreferenceScorer()
        feed_items = []

        for deal in deals:
            confidence = float(
                deal.get(
                    "confidence_score",
                    deal.get("confidence", 0),
                )
            )

            if confidence < minimum_confidence:
                continue

            personalized = scorer.score(
                deal=deal,
                preferences=preferences,
            )

            if not personalized["eligible"]:
                continue

            feed_items.append(
                {
                    **deal,
                    "personalized_score": (
                        personalized[
                            "personalized_score"
                        ]
                    ),
                    "personalization_reasons": (
                        personalized["reasons"]
                    ),
                }
            )

        feed_items.sort(
            key=lambda item: (
                item["personalized_score"],
                float(
                    item.get(
                        "observed_discount_pct",
                        0,
                    )
                ),
                -float(
                    item.get(
                        "effective_price",
                        item.get("price", 0),
                    )
                ),
            ),
            reverse=True,
        )

        limited = feed_items[:max(limit, 0)]

        return {
            "feed_count": len(limited),
            "total_eligible_count": len(
                feed_items
            ),
            "items": limited,
            "metadata": {
                "feed_version": "deal_feed_v1"
            },
        }


class DealFeedService:
    def __init__(self) -> None:
        self.identity = ProductIdentityResolver()
        self.deduplicator = OfferDeduplicator()
        self.feed_builder = DealFeedBuilder()
        self._deals: dict[str, dict[str, Any]] = {}

    def ingest_deals(
        self,
        *,
        deals: list[dict[str, Any]],
    ) -> dict[str, Any]:
        resolved = []

        for deal in deals:
            identity = self.identity.resolve(
                offer=deal
            )

            if not identity["resolved"]:
                continue

            resolved.append(
                {
                    **deal,
                    "canonical_product_key": (
                        identity["product_key"]
                    ),
                    "identity_confidence": (
                        identity["confidence"]
                    ),
                }
            )

        deduplicated = (
            self.deduplicator.deduplicate(
                offers=resolved
            )
        )

        stored = []

        for deal in deduplicated["offers"]:
            deal_id = str(
                deal.get("deal_id")
                or uuid4()
            )

            stored_item = {
                **deal,
                "deal_id": deal_id,
                "ingested_at": now_iso(),
            }

            self._deals[deal_id] = stored_item
            stored.append(stored_item)

        return {
            "input_count": len(deals),
            "resolved_count": len(resolved),
            "stored_count": len(stored),
            "duplicate_count": deduplicated[
                "duplicate_count"
            ],
            "deals": deepcopy(stored),
            "metadata": {
                "service_version": "deal_feed_service_v1"
            },
        }

    def get_feed(
        self,
        *,
        preferences: dict[str, Any] | None = None,
        minimum_confidence: float = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        return self.feed_builder.build(
            deals=list(self._deals.values()),
            preferences=preferences,
            minimum_confidence=minimum_confidence,
            limit=limit,
        )

    def get_deal(
        self,
        deal_id: str,
    ) -> dict[str, Any] | None:
        item = self._deals.get(deal_id)
        return deepcopy(item) if item else None

    def clear(self) -> dict[str, Any]:
        self._deals.clear()
        return {"cleared": True}
