def serialize_agent_decision(decision):
    return {
        "agent_run_id": decision.agent_run_id,
        "user_id": decision.user_id,
        "query": decision.query,
        "decision": decision.decision,
        "confidence": decision.confidence,
        "top_offer": decision.top_offer,
        "personalization": decision.personalization,
        "search": decision.search,
        "matching": decision.matching,
        "price_history": decision.price_history,
        "reasons": decision.reasons,
        "next_actions": decision.next_actions,
        "metadata": decision.metadata,
        "created_at": decision.created_at.isoformat(),
    }
