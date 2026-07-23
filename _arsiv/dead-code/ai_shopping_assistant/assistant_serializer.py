def serialize_shopping_assistant_advice(advice):
    return {
        "assistant_decision": advice.assistant_decision,
        "headline": advice.headline,
        "summary": advice.summary,
        "confidence": advice.confidence,
        "risk_level": advice.risk_level,
        "opportunity_level": advice.opportunity_level,
        "next_actions": advice.next_actions,
        "reason_codes": advice.reason_codes,
        "explanation": advice.explanation,
        "assistant_context": advice.assistant_context,
    }
