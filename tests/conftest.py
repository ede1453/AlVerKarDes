import pytest

from app.domains.cache.cache_repository_factory import get_cache_repository


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    cache = get_cache_repository()

    try:
        cache.clear()
    except Exception:
        pass

    yield

    try:
        cache.clear()
    except Exception:
        pass