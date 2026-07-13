def serialize_unified_search_result(result):
    return {
        "search_id": result.search_id,
        "query": result.query,
        "user_id": result.user_id,
        "status": result.status,
        "aggregation": result.aggregation,
        "top_offer": result.top_offer,
        "candidate_count": result.candidate_count,
        "metadata": result.metadata,
        "created_at": result.created_at.isoformat(),
    }
