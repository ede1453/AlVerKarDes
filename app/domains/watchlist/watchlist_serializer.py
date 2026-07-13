def serialize_watchlist_item(item):
    return {
        "id": item.id,
        "user_id": item.user_id,
        "product_key": item.product_key,
        "query": item.query,
        "target_price": item.target_price,
        "marketplaces": item.marketplaces,
        "channels": item.channels,
        "status": item.status,
        "last_evaluation": item.last_evaluation,
        "metadata": item.metadata,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }
