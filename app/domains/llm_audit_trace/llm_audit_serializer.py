def serialize_llm_audit_trace(record):
    return {
        "id": record.id,
        "provider": record.provider,
        "model": record.model,
        "status": record.status,
        "assistant_decision": record.assistant_decision,
        "prompt_hash": record.prompt_hash,
        "prompt_version": record.prompt_version,
        "safety_warnings": record.safety_warnings,
        "usage": record.usage,
        "metadata": record.metadata,
        "created_at": record.created_at.isoformat(),
    }
