def serialize_deal_score_result(result):
    return {
        "score": result.score,
        "decision": result.decision,
        "reasons": result.reasons,
    }
