def serialize_llm_orchestration_result(result):
    return {
        "status": result.status,
        "selected_provider": result.selected_provider,
        "generated_text": result.generated_text,
        "attempts": [
            {
                "provider": attempt.provider,
                "status": attempt.status,
                "generated_text": attempt.generated_text,
                "safety_warnings": attempt.safety_warnings,
                "metadata": attempt.metadata,
                "attempt_index": attempt.attempt_index,
                "retry_decision": attempt.retry_decision,
                "timeout_classification": attempt.timeout_classification,
            }
            for attempt in result.attempts
        ],
        "fallback_used": result.fallback_used,
        "prompt_version": result.prompt_version,
        "metadata": result.metadata,
    }
