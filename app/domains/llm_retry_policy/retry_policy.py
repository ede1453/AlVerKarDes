from app.domains.llm_retry_policy.retry_models import RetryDecision, RetryPolicyConfig


class ExponentialBackoffRetryPolicy:
    def __init__(self, config: RetryPolicyConfig | None = None):
        self.config = config or RetryPolicyConfig()

    def decide(self, *, status: str, attempt_index: int) -> RetryDecision:
        next_attempt_index = attempt_index + 1

        if status not in self.config.retryable_statuses:
            return RetryDecision(
                should_retry=False,
                next_attempt_index=next_attempt_index,
                delay_ms=0,
                reason="NON_RETRYABLE_STATUS",
            )

        if next_attempt_index >= self.config.max_attempts:
            return RetryDecision(
                should_retry=False,
                next_attempt_index=next_attempt_index,
                delay_ms=0,
                reason="MAX_ATTEMPTS_REACHED",
            )

        return RetryDecision(
            should_retry=True,
            next_attempt_index=next_attempt_index,
            delay_ms=self.delay_for_attempt(next_attempt_index),
            reason="RETRYABLE_STATUS",
        )

    def delay_for_attempt(self, attempt_index: int) -> int:
        raw_delay = self.config.base_delay_ms * (
            self.config.backoff_multiplier ** max(0, attempt_index - 1)
        )
        return int(min(raw_delay, self.config.max_delay_ms))
