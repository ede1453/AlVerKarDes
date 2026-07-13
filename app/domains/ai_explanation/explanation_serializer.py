def serialize_explanation(result):
    return {
        "explanation_id": result.explanation_id,
        "mode": result.mode,
        "language": result.language,
        "tone": result.tone,
        "headline": result.headline,
        "explanation_text": result.explanation_text,
        "bullet_points": result.bullet_points,
        "risk_notes": result.risk_notes,
        "next_actions": result.next_actions,
        "source_signals": result.source_signals,
        "metadata": result.metadata,
        "created_at": result.created_at.isoformat(),
    }
