def serialize_provider_health_status(status):
    return {
        "provider": status.provider,
        "status": status.status,
        "available": status.available,
        "latency_ms": status.latency_ms,
        "success_rate": status.success_rate,
        "failure_count": status.failure_count,
        "last_error": status.last_error,
        "metadata": status.metadata,
    }


def serialize_provider_health_summary(summary):
    return {
        "status": summary.status,
        "healthy_count": summary.healthy_count,
        "degraded_count": summary.degraded_count,
        "unavailable_count": summary.unavailable_count,
        "providers": [
            serialize_provider_health_status(provider)
            for provider in summary.providers
        ],
    }
