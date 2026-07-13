def serialize_decision_context(context):
    return {
        "context_id": context.context_id,
        "created_at": context.created_at.isoformat(),
        "product_id": context.product_id,
        "offer_id": context.offer_id,
        "market": context.market,
        "scores": context.scores,
        "recommendation": context.recommendation,
        "decision": context.decision,
        "trace": context.trace,
        "metadata": context.metadata,
    }
