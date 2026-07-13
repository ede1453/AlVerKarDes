def serialize_canonical_product(product):
    return {
        "canonical_id": product.canonical_id,
        "canonical_key": product.canonical_key,
        "product_name": product.product_name,
        "brand": product.brand,
        "model": product.model,
        "variant": product.variant,
        "category": product.category,
        "confidence": product.confidence,
        "source_offer_ids": product.source_offer_ids,
        "attributes": product.attributes,
        "metadata": product.metadata,
        "created_at": product.created_at.isoformat(),
    }


def serialize_canonicalization_result(result):
    return {
        "query": result.query,
        "canonical_count": result.canonical_count,
        "products": [serialize_canonical_product(product) for product in result.products],
        "metadata": result.metadata,
    }
