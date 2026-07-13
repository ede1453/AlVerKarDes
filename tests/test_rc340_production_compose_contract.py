from pathlib import Path


def test_rc340_compose_exposes_api_for_local_smoke_test():
    text = Path(
        "deploy/docker/docker-compose.production.yml"
    ).read_text(encoding="utf-8")

    assert '"8000:8000"' in text
    assert "profiles:" in text
    assert "- edge" in text
    assert "name: aici-production" in text
