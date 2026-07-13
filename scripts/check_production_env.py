from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse

REQUIRED = {
    "APP_ENV",
    "DATABASE_URL",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "REDIS_URL",
    "JWT_SECRET",
    "CORS_ALLOWED_ORIGINS",
    "AICI_API_PORT",
}

PLACEHOLDER_MARKERS = {
    "CHANGE_ME",
    "YOUR_DOMAIN",
}

path = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else ".env.production"
)

if not path.exists():
    raise SystemExit(
        f"Missing environment file: {path}"
    )

values: dict[str, str] = {}

for line in path.read_text(
    encoding="utf-8"
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

missing = sorted(REQUIRED - values.keys())

placeholders = sorted(
    key
    for key, value in values.items()
    if any(
        marker.lower() in value.lower()
        for marker in PLACEHOLDER_MARKERS
    )
)

errors: list[str] = []

if values.get("APP_ENV") != "production":
    errors.append(
        "APP_ENV must be production"
    )

jwt_secret = values.get("JWT_SECRET", "")

if len(jwt_secret) < 32:
    errors.append(
        "JWT_SECRET must contain at least 32 characters"
    )

database_url = values.get("DATABASE_URL", "")

if database_url:
    if not database_url.startswith(
        "postgresql+asyncpg://"
    ):
        errors.append(
            "DATABASE_URL must use postgresql+asyncpg:// "
            "because requirements.txt provides asyncpg"
        )

    parsed = urlparse(
        database_url.replace(
            "postgresql+asyncpg://",
            "postgresql://",
            1,
        )
    )

    configured_password = values.get(
        "POSTGRES_PASSWORD"
    )

    if (
        parsed.password
        and configured_password
        and parsed.password
        != configured_password
    ):
        errors.append(
            "DATABASE_URL password and "
            "POSTGRES_PASSWORD do not match"
        )

port_value = values.get("AICI_API_PORT", "")

try:
    port = int(port_value)
except ValueError:
    errors.append(
        "AICI_API_PORT must be an integer"
    )
else:
    if not (1024 <= port <= 65535):
        errors.append(
            "AICI_API_PORT must be between 1024 and 65535"
        )

if missing or placeholders or errors:
    raise SystemExit(
        "Environment invalid. "
        f"Missing={missing}; "
        f"placeholders={placeholders}; "
        f"errors={errors}"
    )

print(
    "Production environment check passed."
)
