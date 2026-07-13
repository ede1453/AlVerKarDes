
from app.domains.connectors.manager import UnifiedOffer


class ConnectorSearchPresenter:
    def present(self, *, query: str, country: str, offers: list[UnifiedOffer], errors: list[dict]) -> dict:
        groups = self._group_offers(offers)

        return {
            "query": query,
            "country": country,
            "group_count": len(groups),
            "offer_count": len(offers),
            "groups": groups,
            "errors": errors,
        }

    def _group_offers(self, offers: list[UnifiedOffer]) -> list[dict]:
        grouped: dict[str, list[UnifiedOffer]] = {}

        for offer in offers:
            key = offer.match_group_id or offer.canonical_key or offer.title
            grouped.setdefault(key, []).append(offer)

        result = []

        for group_id, group_offers in grouped.items():
            sorted_offers = sorted(
                group_offers,
                key=lambda item: (
                    item.price is None,
                    item.price if item.price is not None else 10**12,
                    -item.overall_confidence,
                ),
            )

            best = sorted_offers[0]
            prices = [offer.price for offer in sorted_offers if offer.price is not None]

            result.append({
                "match_group_id": group_id,
                "representative_title": best.title,
                "canonical_key": best.canonical_key,
                "offer_count": len(sorted_offers),
                "best_offer": self._offer_to_dict(best),
                "price_range": {
                    "min": min(prices) if prices else None,
                    "max": max(prices) if prices else None,
                    "currency": best.currency,
                },
                "confidence": {
                    "best_overall": best.overall_confidence,
                    "best_match_group_score": best.match_group_score,
                    "average_overall": round(
                        sum(offer.overall_confidence for offer in sorted_offers) / len(sorted_offers),
                        2,
                    ),
                },
                "offers": [self._offer_to_dict(offer) for offer in sorted_offers],
            })

        result.sort(
            key=lambda group: (
                group["best_offer"]["price"] is None,
                group["best_offer"]["price"] if group["best_offer"]["price"] is not None else 10**12,
                -group["confidence"]["best_overall"],
            )
        )

        return result

    def _offer_to_dict(self, offer: UnifiedOffer) -> dict:
        return {
            "source": offer.source,
            "title": offer.title,
            "url": offer.url,
            "price": offer.price,
            "currency": offer.currency,
            "availability": offer.availability,
            "brand": offer.brand,
            "gtin": offer.gtin,
            "sku": offer.sku,
            "canonical_key": offer.canonical_key,
            "connector_confidence": offer.connector_confidence,
            "canonical_confidence": offer.canonical_confidence,
            "overall_confidence": offer.overall_confidence,
            "match_group_id": offer.match_group_id,
            "match_group_score": offer.match_group_score,
            "match_basis": offer.match_basis,
        }
