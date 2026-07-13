from pathlib import Path

from scripts.check_docker_db_env_consistency import (
    check_docker_db_env_consistency,
    extract_compose_env_files,
    normalize_database_url,
)


def make_temp_workspace(name: str) -> Path:
    path = Path(".test_workspaces") / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_rc614_database_url_parser_extracts_credentials():
    parsed = normalize_database_url("postgresql+asyncpg://postgres:password@aici-db:5432/aici")

    assert parsed["user"] == "postgres"
    assert parsed["password"] == "password"
    assert parsed["host"] == "aici-db"
    assert parsed["database"] == "aici"


def test_rc614_guard_detects_password_mismatch():
    tmp_path = make_temp_workspace("password_mismatch")
    compose = tmp_path / "docker-compose.prod.yml"
    env = tmp_path / ".env"

    compose.write_text(
        '''
services:
  aici-db:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: correct-password
      POSTGRES_DB: aici
  aici-api:
    image: app
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:wrong-password@aici-db:5432/aici
''',
        encoding="utf-8",
    )
    env.write_text("", encoding="utf-8")

    issues = check_docker_db_env_consistency(compose, env)

    assert any(issue["code"] == "DATABASE_PASSWORD_MISMATCH" for issue in issues)


def test_rc614_guard_passes_when_compose_credentials_match():
    tmp_path = make_temp_workspace("credentials_match")
    compose = tmp_path / "docker-compose.prod.yml"
    env = tmp_path / ".env"

    compose.write_text(
        '''
services:
  aici-db:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: aici
  aici-api:
    image: app
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:password@aici-db:5432/aici
''',
        encoding="utf-8",
    )
    env.write_text("", encoding="utf-8")

    assert check_docker_db_env_consistency(compose, env) == []


def test_rc614_guard_reads_service_env_file():
    tmp_path = make_temp_workspace("service_env_file")
    compose = tmp_path / "docker-compose.prod.yml"
    env = tmp_path / ".env.prod"

    compose.write_text(
        '''
services:
  aici-db:
    image: postgres:16
    env_file:
      - .env.prod
  aici-api:
    image: app
    env_file:
      - .env.prod
''',
        encoding="utf-8",
    )
    env.write_text(
        "\n".join(
            [
                "POSTGRES_USER=postgres",
                "POSTGRES_PASSWORD=password",
                "POSTGRES_DB=aici",
                "DATABASE_URL=postgresql+asyncpg://postgres:password@aici-db:5432/aici",
            ]
        ),
        encoding="utf-8",
    )

    assert extract_compose_env_files(compose.read_text(encoding="utf-8"), "aici-api") == [".env.prod"]
    assert check_docker_db_env_consistency(compose, env) == []


def test_rc614_guard_detects_unmatched_database_host():
    tmp_path = make_temp_workspace("unmatched_database_host")
    compose = tmp_path / "docker-compose.prod.yml"
    env = tmp_path / ".env"

    compose.write_text(
        '''
services:
  aici-db:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: aici
  aici-api:
    image: app
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:password@db:5432/aici
''',
        encoding="utf-8",
    )
    env.write_text("", encoding="utf-8")

    issues = check_docker_db_env_consistency(compose, env)

    assert any(issue["code"] == "DATABASE_HOST_SERVICE_NOT_MATCHED" for issue in issues)
