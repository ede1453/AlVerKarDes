from app.domains.llm_retry_policy.retry_models import RetryPolicyConfig
from app.domains.llm_retry_policy.retry_policy import ExponentialBackoffRetryPolicy


def test_retry_policy_retries_retryable_status_with_backoff():
    policy = ExponentialBackoffRetryPolicy(
        RetryPolicyConfig(max_attempts=3, base_delay_ms=100, max_delay_ms=1000)
    )

    decision = policy.decide(status="PROVIDER_NOT_CONFIGURED", attempt_index=0)

    assert decision.should_retry is True
    assert decision.next_attempt_index == 1
    assert decision.delay_ms == 100
    assert decision.reason == "RETRYABLE_STATUS"


def test_retry_policy_stops_at_max_attempts():
    policy = ExponentialBackoffRetryPolicy(RetryPolicyConfig(max_attempts=2))

    decision = policy.decide(status="PROVIDER_NOT_CONFIGURED", attempt_index=1)

    assert decision.should_retry is False
    assert decision.reason == "MAX_ATTEMPTS_REACHED"


def test_retry_policy_does_not_retry_blocked_status():
    decision = ExponentialBackoffRetryPolicy().decide(status="BLOCKED", attempt_index=0)

    assert decision.should_retry is False
    assert decision.reason == "NON_RETRYABLE_STATUS"
