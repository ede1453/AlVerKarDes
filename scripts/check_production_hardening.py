from __future__ import annotations

import json
import os
from pathlib import Path

from app.core.production_hardening import (
    evaluate_environment,
    required_connector_credentials,
)


def read_env(path: Path) -> dict[str, str]:
    values = {}

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


path = Path(".env.production")

if not path.exists():
    raise SystemExit(
        "Missing .env.production"
    )

environment = read_env(path)
environment.update({
    key: value
    for key, value in os.environ.items()
    if key not in environment
})

result = evaluate_environment(environment)
connectors = required_connector_credentials(
    environment
)

report = {
    "environment": result,
    "connectors": connectors,
}

print(
    json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
    )
)

if not result["ready"]:
    raise SystemExit(
        "Production environment hardening failed."
    )
