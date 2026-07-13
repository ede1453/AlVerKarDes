def serialize_retry_decision(decision):
    return {
        "should_retry": decision.should_retry,
        "next_attempt_index": decision.next_attempt_index,
        "delay_ms": decision.delay_ms,
        "reason": decision.reason,
    }
