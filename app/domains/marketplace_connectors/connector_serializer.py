def serialize_offer(offer):
    return {
        "id": offer.id,
        "marketplace": offer.marketplace,
        "seller": offer.seller,
        "product_name": offer.product_name,
        "price": offer.price,
        "currency": offer.currency,
        "url": offer.url,
        "availability": offer.availability,
        "metadata": offer.metadata,
        "collected_at": offer.collected_at.isoformat(),
    }


def serialize_result(result):
    return {
        "marketplace": result.marketplace,
        "query": result.query,
        "status": result.status,
        "offer_count": result.offer_count,
        "offers": [serialize_offer(offer) for offer in result.offers],
        "metadata": result.metadata,
    }
