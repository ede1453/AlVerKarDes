from datetime import timedelta

RETRY_POLICY = {
    1: timedelta(minutes=1),
    2: timedelta(minutes=5),
    3: timedelta(minutes=30),
    4: timedelta(hours=2),
    5: timedelta(hours=12),
}


def get_retry_delay(retry_number: int) -> timedelta | None:
    return RETRY_POLICY.get(retry_number)


def should_dead_letter(retry_count: int, max_retries: int) -> bool:
    return retry_count >= max_retries
