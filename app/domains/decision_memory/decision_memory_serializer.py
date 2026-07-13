def serialize_decision_memory(record):
    return {
        "id": record.id,
        "product_id": record.product_id,
        "offer_id": record.offer_id,
        "country": record.country,
        "final_decision": record.final_decision,
        "confidence": record.confidence,
        "risk_level": record.risk_level,
        "opportunity_level": record.opportunity_level,
        "deal_score": record.deal_score,
        "authenticity_score": record.authenticity_score,
        "recommendation": record.recommendation,
        "reason_codes": record.reason_codes,
        "decision_context": record.decision_context,
        "generated_at": record.generated_at.isoformat(),
        "outcome": record.outcome,
    }
