def serialize_consumer_intelligence(result):
    return {
        "final_decision": result.final_decision,
        "confidence": result.confidence,
        "risk_level": result.risk_level,
        "opportunity_level": result.opportunity_level,
        "reason_codes": result.reason_codes,
        "explanation": result.explanation,
    }
