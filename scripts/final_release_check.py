from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE_URL = (
    sys.argv[1].rstrip("/")
    if len(sys.argv) > 1
    else "http://127.0.0.1:8000"
)

COMPOSE_FILE = (
    sys.argv[2]
    if len(sys.argv) > 2
    else r".\deploy\docker\docker-compose.production.yml"
)

ENV_FILE = (
    sys.argv[3]
    if len(sys.argv) > 3
    else r".\.env.production"
)

results: dict[str, object] = {
    "base_url": BASE_URL,
    "test_environment": "host_active_virtualenv",
    "runtime_environment": "production_api_container",
    "checks": {},
}


def run_command(
    command: list[str],
    *,
    environment: dict[str, str] | None = None,
) -> tuple[bool, str]:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )

    output = (
        completed.stdout
        + completed.stderr
    ).strip()

    return completed.returncode == 0, output


required_files = [
    "deploy/docker/Dockerfile.production",
    "deploy/docker/docker-compose.production.yml",
    "scripts/production_smoke_test.py",
    "scripts/check_openapi_uniqueness.py",
    "scripts/api_contract_schema_guard.py",
    "scripts/check_docker_db_env_consistency.py",
    "scripts/validate_release_manifest.py",
]

missing = [
    item
    for item in required_files
    if not Path(item).exists()
]

results["checks"]["required_files"] = {
    "passed": not missing,
    "missing": missing,
}

for path in ["/health", "/openapi.json"]:
    try:
        with urllib.request.urlopen(
            BASE_URL + path,
            timeout=15,
        ) as response:
            passed = response.status == 200
            status = response.status
    except Exception as exc:
        passed = False
        status = str(exc)

    results["checks"][f"http:{path}"] = {
        "passed": passed,
        "status": status,
    }

try:
    with urllib.request.urlopen(
        BASE_URL + "/api/v1/connector-operations/readiness",
        timeout=15,
    ) as response:
        readiness_payload = json.loads(response.read().decode("utf-8"))
        readiness_status = readiness_payload.get("status")
        readiness_summary = readiness_payload.get("summary", {})
        readiness_connectors = readiness_payload.get("connectors", [])
        readiness_passed = (
            response.status == 200
            and readiness_status in {"READY", "ACTION_REQUIRED"}
            and isinstance(readiness_summary.get("connector_count"), int)
            and isinstance(readiness_connectors, list)
        )
except Exception as exc:
    readiness_status = str(exc)
    readiness_summary = {}
    readiness_connectors = []
    readiness_passed = False

results["checks"]["connector_readiness"] = {
    "passed": readiness_passed,
    "status": readiness_status,
    "summary": readiness_summary,
    "connector_count": len(readiness_connectors),
    "note": (
        "ACTION_REQUIRED can be acceptable during staged production when "
        "mock/fixture connectors are intentionally enabled."
    ),
}

compose_prefix = [
    "docker",
    "compose",
    "--env-file",
    ENV_FILE,
    "-f",
    COMPOSE_FILE,
]

container_ok, container_output = run_command(
    compose_prefix
    + [
        "ps",
        "--status",
        "running",
        "api",
    ]
)

results["checks"]["production_container_running"] = {
    "passed": (
        container_ok
        and "api" in container_output.lower()
        and "healthy" in container_output.lower()
    ),
    "environment": "production_api_container",
    "output": container_output,
}

# Test suite is intentionally executed in the active host virtualenv.
# The production image should not contain pytest or development dependencies.
pytest_ok, pytest_output = run_command(
    [
        sys.executable,
        "-m",
        "pytest",
        "-q",
    ]
)

results["checks"]["pytest"] = {
    "passed": pytest_ok,
    "environment": "host_active_virtualenv",
    "python_executable": sys.executable,
    "output_tail": pytest_output[-5000:],
}

host_checks = {
    "openapi_uniqueness": [
        sys.executable,
        "scripts/check_openapi_uniqueness.py",
    ],
    "api_schema_guard": [
        sys.executable,
        "scripts/api_contract_schema_guard.py",
    ],
    "docker_db_env_consistency": [
        sys.executable,
        "scripts/check_docker_db_env_consistency.py",
    ],
    "release_manifest": [
        sys.executable,
        "scripts/validate_release_manifest.py",
    ],
}

for check_name, command in host_checks.items():
    passed, output = run_command(command)
    results["checks"][check_name] = {
        "passed": passed,
        "environment": "host_active_virtualenv",
        "output": output,
    }

# Container checks only production runtime dependencies and imports.
runtime_import_ok, runtime_import_output = run_command(
    compose_prefix
    + [
        "exec",
        "-T",
        "api",
        "python",
        "-c",
        (
            "import asyncpg; "
            "from app.main import app; "
            "print('production runtime imports passed'); "
            "print(len(app.routes))"
        ),
    ]
)

results["checks"]["production_runtime_imports"] = {
    "passed": runtime_import_ok,
    "environment": "production_api_container",
    "output": runtime_import_output,
}

alembic_ok, alembic_output = run_command(
    compose_prefix
    + [
        "run",
        "--rm",
        "api",
        "alembic",
        "current",
    ]
)

results["checks"]["alembic_head"] = {
    "passed": (
        alembic_ok
        and "0014_deal_storage_sqlalchemy" in alembic_output
        and "(head)" in alembic_output
    ),
    "environment": "production_api_container",
    "output": alembic_output,
}

all_passed = all(
    bool(item.get("passed"))
    for item in results["checks"].values()
)

results["go_no_go"] = (
    "GO"
    if all_passed
    else "NO_GO"
)

Path("release").mkdir(
    parents=True,
    exist_ok=True,
)

Path(
    "release/final_release_check.json"
).write_text(
    json.dumps(
        results,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)

print(
    json.dumps(
        results,
        indent=2,
        ensure_ascii=False,
    )
)

if not all_passed:
    raise SystemExit(1)

