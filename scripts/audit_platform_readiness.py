from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import os
import re
import subprocess

from app.core.production_hardening import (
    evaluate_environment,
    path_is_release_safe,
    redacted_environment,
    required_connector_credentials,
    route_auth_coverage,
)


ROOT = Path(".")
APP_DIR = ROOT / "app"
TEST_DIR = ROOT / "tests"


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip()


def read_env_file(path: Path) -> dict[str, str]:
    values = {}

    if not path.exists():
        return values

    for line in path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).splitlines():
        stripped = line.strip()

        if (
            not stripped
            or stripped.startswith("#")
            or "=" not in stripped
        ):
            continue

        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()

    return values


def route_rows() -> list[dict]:
    from fastapi.routing import APIRoute
    from app.main import app

    rows = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        dependency_names = {
            getattr(dependency.call, "__name__", "")
            for dependency in route.dependant.dependencies
        }

        protected = any(
            name in dependency_names
            for name in (
                "get_current_user",
                "require_admin",
                "require_api_key",
            )
        )

        rows.append({
            "path": route.path,
            "methods": sorted(route.methods or []),
            "operation_id": route.operation_id,
            "protected": protected,
        })

    return rows


def main() -> None:
    all_files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
    ]

    unsafe_files = [
        str(path)
        for path in all_files
        if not path_is_release_safe(
            str(path.relative_to(ROOT))
        )
    ]

    test_files = list(
        TEST_DIR.glob("test_*.py")
    )

    router_files = list(
        (APP_DIR / "api" / "v1").glob("*router.py")
    )

    env_values = read_env_file(
        ROOT / ".env.production"
    )
    env_values.update({
        key: value
        for key, value in os.environ.items()
        if key not in env_values
    })

    routes = route_rows()
    duplicate_pairs = [
        {
            "method": method,
            "path": path,
            "count": count,
        }
        for (method, path), count in Counter(
            (
                method,
                row["path"],
            )
            for row in routes
            for method in row["methods"]
            if method not in {"HEAD", "OPTIONS"}
        ).items()
        if count > 1
    ]

    report = {
        "summary": {
            "file_count": len(all_files),
            "python_file_count": len(
                list(ROOT.rglob("*.py"))
            ),
            "test_file_count": len(test_files),
            "router_file_count": len(router_files),
            "route_count": len(routes),
            "migration_count": len(
                list(
                    (ROOT / "alembic" / "versions")
                    .glob("*.py")
                )
            ),
        },
        "release_hygiene": {
            "unsafe_file_count": len(unsafe_files),
            "unsafe_files_sample": unsafe_files[:100],
            "git_dirty": bool(
                git_output("status", "--porcelain")
            ),
            "git_tag": git_output(
                "describe",
                "--tags",
                "--exact-match",
            ),
        },
        "environment": evaluate_environment(
            env_values
        ),
        "connector_credentials": (
            required_connector_credentials(
                env_values
            )
        ),
        "routing": {
            "duplicate_route_count": len(
                duplicate_pairs
            ),
            "duplicates": duplicate_pairs,
        },
        "authorization": route_auth_coverage(
            routes
        ),
        "redacted_environment": (
            redacted_environment(env_values)
        ),
    }

    output = ROOT / "release" / "platform_readiness_audit.json"
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
