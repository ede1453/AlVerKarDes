def _decimal_to_string(value):
    if value is None:
        return None
    return str(value)


def serialize_marketplace_offer(offer):
    return {
        "id": offer.id,
        "marketplace": offer.marketplace,
        "seller": offer.seller,
        "product_name": offer.product_name,
        "normalized_product_name": offer.normalized_product_name,
        "price": str(offer.price),
        "currency": offer.currency,
        "url": offer.url,
        "availability": offer.availability,
        "metadata": offer.metadata,
        "collected_at": offer.collected_at.isoformat(),
    }


def serialize_marketplace_aggregation(result):
    return {
        "query": result.query,
        "normalized_query": result.normalized_query,
        "offer_count": result.offer_count,
        "marketplaces": result.marketplaces,
        "min_price": _decimal_to_string(result.min_price),
        "max_price": _decimal_to_string(result.max_price),
        "currency": result.currency,
        "offers": [serialize_marketplace_offer(offer) for offer in result.offers],
    }
