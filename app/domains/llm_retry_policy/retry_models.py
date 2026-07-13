from dataclasses import dataclass, field


@dataclass
class RetryPolicyConfig:
    max_attempts: int = 3
    base_delay_ms: int = 100
    max_delay_ms: int = 2000
    backoff_multiplier: float = 2.0
    retryable_statuses: set[str] = field(
        default_factory=lambda: {
            "PROVIDER_NOT_FOUND",
            "PROVIDER_NOT_CONFIGURED",
            "NOT_IMPLEMENTED",
            "TIMEOUT",
            "TEMPORARY_ERROR",
        }
    )


@dataclass
class RetryDecision:
    should_retry: bool
    next_attempt_index: int
    delay_ms: int
    reason: str
