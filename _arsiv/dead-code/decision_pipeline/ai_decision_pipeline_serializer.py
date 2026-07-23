def serialize_ai_decision_pipeline(result):
    return {
        "pipeline_status": result.pipeline_status,
        "final_decision": result.final_decision,
        "confidence": result.confidence,
        "risk_level": result.risk_level,
        "opportunity_level": result.opportunity_level,
        "reason_codes": result.reason_codes,
        "explanation": result.explanation,
        "stages": result.stages,
    }
