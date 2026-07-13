def serialize_recommendation_intelligence(result):
    return {
        "recommendation": result.recommendation,
        "confidence": result.confidence,
        "reason_codes": result.reason_codes,
        "explanation": result.explanation,
    }
