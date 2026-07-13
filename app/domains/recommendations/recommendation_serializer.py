def serialize_recommendation_item(item):
    return {
        "recommendation_id": item.recommendation_id,
        "product_key": item.product_key,
        "product_name": item.product_name,
        "recommendation_type": item.recommendation_type,
        "score": item.score,
        "rank": item.rank,
        "rationale": item.rationale,
        "source": item.source,
        "metadata": item.metadata,
    }


def serialize_recommendation_result(result):
    return {
        "run_id": result.run_id,
        "user_id": result.user_id,
        "query": result.query,
        "status": result.status,
        "items": [serialize_recommendation_item(item) for item in result.items],
        "next_actions": result.next_actions,
        "metadata": result.metadata,
        "created_at": result.created_at.isoformat(),
    }
