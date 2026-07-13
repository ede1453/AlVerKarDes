def serialize_provider_selection_candidate(candidate):
    return {
        "provider": candidate.provider,
        "health_status": candidate.health_status,
        "available": candidate.available,
        "latency_ms": candidate.latency_ms,
        "success_rate": candidate.success_rate,
        "selection_score": candidate.selection_score,
        "reasons": candidate.reasons,
    }


def serialize_provider_selection_result(result):
    return {
        "selected_provider": result.selected_provider,
        "fallback_providers": result.fallback_providers,
        "candidates": [
            serialize_provider_selection_candidate(candidate)
            for candidate in result.candidates
        ],
        "strategy": result.strategy,
        "metadata": result.metadata,
    }
