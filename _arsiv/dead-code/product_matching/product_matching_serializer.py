def serialize_candidate(candidate):
    return {
        "offer_id": candidate.offer_id,
        "marketplace": candidate.marketplace,
        "product_name": candidate.product_name,
        "normalized_product_name": candidate.normalized_product_name,
        "price": candidate.price,
        "currency": candidate.currency,
        "metadata": candidate.metadata,
    }


def serialize_group(group):
    return {
        "group_id": group.group_id,
        "canonical_name": group.canonical_name,
        "normalized_canonical_name": group.normalized_canonical_name,
        "match_confidence": group.match_confidence,
        "candidates": [serialize_candidate(candidate) for candidate in group.candidates],
        "created_at": group.created_at.isoformat(),
    }


def serialize_matching_result(result):
    return {
        "query": result.query,
        "group_count": result.group_count,
        "matched_offer_count": result.matched_offer_count,
        "groups": [serialize_group(group) for group in result.groups],
        "metadata": result.metadata,
    }
