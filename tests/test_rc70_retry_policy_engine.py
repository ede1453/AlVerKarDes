from datetime import timedelta

from app.domains.notifications.outbox.retry_policy import (
    RETRY_POLICY,
    get_retry_delay,
    should_dead_letter,
)


def test_rc70_retry_policy_defines_expected_backoff_steps():
    assert RETRY_POLICY[1] == timedelta(minutes=1)
    assert RETRY_POLICY[2] == timedelta(minutes=5)
    assert RETRY_POLICY[3] == timedelta(minutes=30)
    assert RETRY_POLICY[4] == timedelta(hours=2)
    assert RETRY_POLICY[5] == timedelta(hours=12)


def test_rc70_get_retry_delay_returns_none_for_unknown_step():
    assert get_retry_delay(99) is None


def test_rc70_should_dead_letter_when_retry_count_reaches_max():
    assert should_dead_letter(retry_count=3, max_retries=3) is True
    assert should_dead_letter(retry_count=2, max_retries=3) is False
