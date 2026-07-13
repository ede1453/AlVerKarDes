def serialize_rate_limit_check(check):
    return {
        "allowed": check.allowed,
        "scope": check.scope,
        "key": check.key,
        "limit": check.limit,
        "remaining": check.remaining,
        "reset_at": check.reset_at.isoformat(),
        "reason": check.reason,
    }
