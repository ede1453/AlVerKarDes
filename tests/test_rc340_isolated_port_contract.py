from pathlib import Path


def test_rc340_compose_uses_local_production_port():
    text = Path(
        "deploy/docker/docker-compose.production.yml"
    ).read_text(encoding="utf-8")

    assert '"8000:8000"' in text
