import re
from pathlib import Path
from urllib.parse import urlparse

COMPOSE_FILE = Path("docker-compose.prod.yml")
ENV_FILE = Path(".env.prod")


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def resolve_env_value(value: str, env: dict[str, str]) -> str:
    match = re.fullmatch(r"\$\{(?P<name>[A-Z0-9_]+):-?(?P<default>[^}]*)\}", value)
    if match:
        return env.get(match.group("name"), match.group("default"))

    match = re.fullmatch(r"\$\{(?P<name>[A-Z0-9_]+)\}", value)
    if match:
        return env.get(match.group("name"), "")

    return value


def normalize_database_url(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    return {
        "scheme": parsed.scheme,
        "user": parsed.username or "",
        "password": parsed.password or "",
        "host": parsed.hostname or "",
        "database": parsed.path.lstrip("/"),
    }


def find_postgres_services(compose_text: str) -> list[str]:
    services = []
    for match in re.finditer(
        r"(?ms)^\s{2}(?P<name>[\w-]+):\s*\n(?P<body>.*?)(?=^\s{2}[\w-]+:\s*\n|\Z)",
        compose_text,
    ):
        if "postgres" in match.group("body").lower():
            services.append(match.group("name"))
    return services


def extract_service_body(compose_text: str, service_name: str) -> str:
    match = re.search(
        rf"(?ms)^\s{{2}}{re.escape(service_name)}:\s*\n(?P<body>.*?)(?=^\s{{2}}[\w-]+:\s*\n|\Z)",
        compose_text,
    )
    if not match:
        return ""
    return match.group("body")


def extract_compose_env_files(compose_text: str, service_name: str) -> list[str]:
    body = extract_service_body(compose_text, service_name)
    if not body:
        return []

    list_match = re.search(r"(?m)^\s{4}env_file:[ \t]*\r?\n(?P<block>(?:^\s{6}-\s+.+\r?\n?)+)", body)
    if list_match:
        return [line.strip()[1:].strip().strip('"').strip("'") for line in list_match.group("block").splitlines()]

    scalar_match = re.search(r"(?m)^\s{4}env_file:[ \t]*(?P<path>.+)$", body)
    if scalar_match:
        return [scalar_match.group("path").strip().strip('"').strip("'")]

    return []


def extract_compose_environment(compose_text: str, service_name: str) -> dict[str, str]:
    body = extract_service_body(compose_text, service_name)
    if not body:
        return {}

    env: dict[str, str] = {}

    list_match = re.search(r"(?m)^\s{4}environment:[ \t]*\r?\n(?P<block>(?:^\s{6}-\s+.+\r?\n?)+)", body)
    if list_match:
        for line in list_match.group("block").splitlines():
            item = line.strip()
            if not item.startswith("-"):
                continue
            item = item[1:].strip()
            if "=" in item:
                key, value = item.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")

    map_match = re.search(r"(?m)^\s{4}environment:[ \t]*\r?\n(?P<block>(?:^\s{6}[\w_]+:[ \t]*.+\r?\n?)+)", body)
    if map_match:
        for line in map_match.group("block").splitlines():
            item = line.strip()
            if ":" in item:
                key, value = item.split(":", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")

    return env


def build_service_environment(
    compose_path: Path,
    compose_text: str,
    service_name: str,
    fallback_env: dict[str, str],
) -> dict[str, str]:
    env = dict(fallback_env)
    for env_file in extract_compose_env_files(compose_text, service_name):
        env.update(parse_env_file((compose_path.parent / env_file).resolve()))
    env.update(extract_compose_environment(compose_text, service_name))
    return {key: resolve_env_value(value, env) for key, value in env.items()}


def check_docker_db_env_consistency(
    compose_path: Path = COMPOSE_FILE,
    env_path: Path = ENV_FILE,
) -> list[dict]:
    issues: list[dict] = []

    if not compose_path.exists():
        return [{"code": "COMPOSE_FILE_MISSING", "message": "docker-compose.prod.yml bulunamadi."}]

    env = parse_env_file(env_path)
    compose_text = compose_path.read_text(encoding="utf-8")

    postgres_services = find_postgres_services(compose_text)
    if not postgres_services:
        return [{"code": "POSTGRES_SERVICE_NOT_FOUND", "message": "Postgres servisi bulunamadi."}]

    api_env = build_service_environment(compose_path, compose_text, "aici-api", env)
    raw_database_url = api_env.get("DATABASE_URL") or env.get("DATABASE_URL")
    if not raw_database_url:
        return [{"code": "DATABASE_URL_NOT_FOUND", "message": "aici-api icin DATABASE_URL bulunamadi."}]

    database_url = resolve_env_value(raw_database_url, api_env)
    db_url = normalize_database_url(database_url)

    matched = False
    for service_name in postgres_services:
        postgres_env = build_service_environment(compose_path, compose_text, service_name, env)

        if db_url["host"] != service_name:
            continue

        matched = True
        postgres_user = postgres_env.get("POSTGRES_USER", "postgres")
        postgres_password = postgres_env.get("POSTGRES_PASSWORD", "")
        postgres_db = postgres_env.get("POSTGRES_DB", "")

        if db_url["user"] != postgres_user:
            issues.append(
                {
                    "code": "DATABASE_USER_MISMATCH",
                    "message": "DATABASE_URL kullanici adi ile POSTGRES_USER uyusmuyor.",
                    "service": service_name,
                    "database_url_user": db_url["user"],
                    "postgres_user": postgres_user,
                }
            )

        if postgres_password and db_url["password"] != postgres_password:
            issues.append(
                {
                    "code": "DATABASE_PASSWORD_MISMATCH",
                    "message": "DATABASE_URL parolasi ile POSTGRES_PASSWORD uyusmuyor.",
                    "service": service_name,
                }
            )

        if postgres_db and db_url["database"] != postgres_db:
            issues.append(
                {
                    "code": "DATABASE_NAME_MISMATCH",
                    "message": "DATABASE_URL database adi ile POSTGRES_DB uyusmuyor.",
                    "service": service_name,
                    "database_url_db": db_url["database"],
                    "postgres_db": postgres_db,
                }
            )

    if not matched:
        issues.append(
            {
                "code": "DATABASE_HOST_SERVICE_NOT_MATCHED",
                "message": "DATABASE_URL host degeri compose icindeki Postgres servis adiyla eslesmiyor.",
                "database_url_host": db_url["host"],
                "postgres_services": postgres_services,
            }
        )

    return issues


def assert_docker_db_env_consistency() -> list[dict]:
    issues = check_docker_db_env_consistency()
    if issues:
        raise AssertionError("Docker DB env consistency check failed: " + repr(issues))
    return issues


if __name__ == "__main__":
    assert_docker_db_env_consistency()
    print("Docker DB env consistency check passed.")
