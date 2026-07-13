def serialize_observability_snapshot(snapshot):
    return {
        "status": snapshot.status,
        "providers": [
            {
                "provider": item.provider,
                "health_status": item.health_status,
                "available": item.available,
                "latency_ms": item.latency_ms,
                "success_rate": item.success_rate,
                "failure_count": item.failure_count,
            }
            for item in snapshot.providers
        ],
        "orchestration": None
        if snapshot.orchestration is None
        else {
            "status": snapshot.orchestration.status,
            "selected_provider": snapshot.orchestration.selected_provider,
            "fallback_used": snapshot.orchestration.fallback_used,
            "attempt_count": snapshot.orchestration.attempt_count,
            "prompt_version": snapshot.orchestration.prompt_version,
        },
        "audit": None
        if snapshot.audit is None
        else {
            "audit_enabled": snapshot.audit.audit_enabled,
            "persistence_mode": snapshot.audit.persistence_mode,
            "prompt_version": snapshot.audit.prompt_version,
        },
        "metadata": snapshot.metadata,
    }
