from pathlib import Path


def test_rc1_deployment_files_exist():
    expected = [
        "Dockerfile",
        "docker-compose.prod.yml",
        ".env.prod.example",
        "scripts/prod_release_check.ps1",
        "RELEASE_CHECKLIST_RC1.md",
    ]

    missing = [item for item in expected if not Path(item).exists()]

    assert missing == []


def test_dockerfile_uses_uvicorn():
    content = Path("Dockerfile").read_text(encoding="utf-8")

    assert "uvicorn" in content
    assert "app.main:app" in content


def test_prod_compose_has_api_and_db():
    content = Path("docker-compose.prod.yml").read_text(encoding="utf-8")

    assert "aici-api" in content
    assert "aici-db" in content
    assert "postgres" in content
