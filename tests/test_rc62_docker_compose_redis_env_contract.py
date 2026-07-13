from pathlib import Path


def test_rc62_env_prod_uses_redis_service_name_when_present():
    env_path = Path(".env.prod")
    if not env_path.exists():
        return

    content = env_path.read_text(encoding="utf-8")

    assert "AICI_REDIS_URL=redis://redis:6379/0" in content
    assert "AICI_REDIS_URL=redis://aici-redis-prod:6379/0" not in content


def test_rc62_compose_declares_redis_service():
    compose_path = Path("docker-compose.prod.yml")
    assert compose_path.exists()

    content = compose_path.read_text(encoding="utf-8")

    assert "redis:" in content
    assert "aici-api:" in content
    assert "aici-db:" in content
