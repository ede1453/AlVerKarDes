def serialize_explanation(result):
    return {
        "headline": result.headline,
        "summary": result.summary,
        "reason_tree": result.reason_tree,
        "confidence_breakdown": result.confidence_breakdown,
        "risk_breakdown": result.risk_breakdown,
        "opportunity_breakdown": result.opportunity_breakdown,
        "llm_prompt_context": result.llm_prompt_context,
    }
