from decimal import Decimal

from app.domains.marketplace_aggregation.marketplace_models import (
    MarketplaceAggregationResult,
    MarketplaceOfferInput,
    create_marketplace_offer,
    normalize_text,
)


class MarketplaceAggregator:
    def aggregate(self, *, query: str, offers: list[dict]) -> MarketplaceAggregationResult:
        normalized_query = normalize_text(query)

        normalized_offers = [
            create_marketplace_offer(
                MarketplaceOfferInput(
                    marketplace=item["marketplace"],
                    seller=item.get("seller") or item["marketplace"],
                    product_name=item["product_name"],
                    price=Decimal(str(item["price"])),
                    currency=item.get("currency", "EUR"),
                    url=item.get("url"),
                    availability=item.get("availability", "UNKNOWN"),
                    metadata=item.get("metadata", {}),
                )
            )
            for item in offers
        ]

        filtered = [
            offer
            for offer in normalized_offers
            if normalized_query in offer.normalized_product_name
            or offer.normalized_product_name in normalized_query
        ]

        if not filtered:
            filtered = normalized_offers

        sorted_offers = sorted(filtered, key=lambda offer: (offer.price, offer.marketplace))
        prices = [offer.price for offer in sorted_offers]
        currencies = list(dict.fromkeys([offer.currency for offer in sorted_offers]))
        marketplaces = list(dict.fromkeys([offer.marketplace for offer in sorted_offers]))

        return MarketplaceAggregationResult(
            query=query,
            normalized_query=normalized_query,
            offer_count=len(sorted_offers),
            marketplaces=marketplaces,
            min_price=min(prices) if prices else None,
            max_price=max(prices) if prices else None,
            currency=currencies[0] if len(currencies) == 1 else None,
            offers=sorted_offers,
        )
