from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
import hashlib
import json
import os
import re


SENSITIVE_NAME_PARTS = (
    "SECRET",
    "PASSWORD",
    "TOKEN",
    "API_KEY",
    "CLIENT_SECRET",
    "PRIVATE_KEY",
)

PLACEHOLDER_MARKERS = (
    "CHANGE_ME",
    "REPLACE_ME",
    "REPLACE_WITH",
    "PLACEHOLDER",
    "EXAMPLE_SECRET",
    "YOUR_",
    # HARDEN-001: a value that spells out what it is ("...SECRET"/"...PASSWORD"/
    # "...TOKEN") is a strong signal of a descriptive/example value rather than
    # a real generated secret -- a real random token essentially never contains
    # these words literally. Found live: the deployed JWT_SECRET was the
    # (Turkish) placeholder text "EN_AZ_32_KARAKTERLIK_GUCLU_RASTGELE_SECRET"
    # ("AT LEAST 32 CHARACTER STRONG RANDOM SECRET"), which the previous
    # marker list did not catch because it only covered English conventions.
    "SECRET",
    "PASSWORD",
    "_TOKEN",
)

PUBLIC_PATHS = {
    "/",
    "/health",
    "/live",
    "/ready",
    "/openapi.json",
    "/docs",
    "/redoc",
}


@dataclass(frozen=True)
class HardeningFinding:
    code: str
    severity: str
    passed: bool
    message: str
    details: dict[str, object]


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def is_placeholder(value: str | None) -> bool:
    normalized = (value or "").strip().upper()
    return (
        not normalized
        or any(marker in normalized for marker in PLACEHOLDER_MARKERS)
    )


def secret_strength(value: str | None, minimum_length: int = 32) -> dict:
    text = value or ""
    classes = sum(
        bool(re.search(pattern, text))
        for pattern in (
            r"[a-z]",
            r"[A-Z]",
            r"[0-9]",
            r"[^A-Za-z0-9]",
        )
    )
    return {
        "valid": (
            len(text) >= minimum_length
            and classes >= 3
            and not is_placeholder(text)
        ),
        "length": len(text),
        "character_classes": classes,
    }


def parse_cors_origins(value: str | None) -> list[str]:
    origins = split_csv(value)
    return [
        origin.rstrip("/")
        for origin in origins
    ]


def validate_cors(
    origins: Iterable[str],
    *,
    production: bool,
) -> dict:
    origins = list(origins)
    errors = []

    if production and not origins:
        errors.append("CORS_ORIGINS_REQUIRED")

    if production and "*" in origins:
        errors.append("CORS_WILDCARD_FORBIDDEN")

    for origin in origins:
        if origin == "*":
            continue
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"INVALID_ORIGIN:{origin}")
        if production and parsed.scheme != "https":
            errors.append(f"HTTPS_REQUIRED:{origin}")

    return {
        "valid": not errors,
        "errors": errors,
        "origins": origins,
    }


def parse_trusted_hosts(value: str | None) -> list[str]:
    return split_csv(value)


def validate_trusted_hosts(
    hosts: Iterable[str],
    *,
    production: bool,
) -> dict:
    hosts = list(hosts)
    errors = []

    if production and not hosts:
        errors.append("TRUSTED_HOSTS_REQUIRED")

    if production and "*" in hosts:
        errors.append("TRUSTED_HOST_WILDCARD_FORBIDDEN")

    return {
        "valid": not errors,
        "errors": errors,
        "hosts": hosts,
    }


# HARDEN-005: unlike CORS/TrustedHosts, MAX_REQUEST_BODY_BYTES already has a
# sane default (2 MiB) and RequestSizeLimitMiddleware is always mounted -- the
# real risk is a misconfigured *value* (zero/negative disables real traffic,
# absurdly large defeats the protection), not a missing/disabled setting.
MIN_SANE_REQUEST_BODY_BYTES = 1024  # 1 KiB -- below this, virtually no real JSON request fits
MAX_SANE_REQUEST_BODY_BYTES = 50 * 1024 * 1024  # 50 MiB -- generous upper bound for a JSON API


def validate_request_body_limit(
    maximum_bytes: int,
    *,
    production: bool,
) -> dict:
    errors = []

    if maximum_bytes <= 0:
        errors.append("REQUEST_BODY_LIMIT_MUST_BE_POSITIVE")
    elif production and maximum_bytes < MIN_SANE_REQUEST_BODY_BYTES:
        errors.append("REQUEST_BODY_LIMIT_TOO_SMALL_FOR_PRODUCTION")
    elif production and maximum_bytes > MAX_SANE_REQUEST_BODY_BYTES:
        errors.append("REQUEST_BODY_LIMIT_TOO_LARGE_FOR_PRODUCTION")

    return {
        "valid": not errors,
        "errors": errors,
        "maximum_bytes": maximum_bytes,
    }


def validate_database_url(
    database_url: str,
    *,
    production: bool,
) -> dict:
    parsed = urlparse(database_url)
    errors = []

    if not parsed.scheme.startswith("postgresql"):
        errors.append("POSTGRESQL_REQUIRED")

    if production and parsed.hostname in {
        "localhost",
        "127.0.0.1",
        None,
    }:
        errors.append("PRODUCTION_DATABASE_HOST_REQUIRED")

    if not parsed.username:
        errors.append("DATABASE_USERNAME_REQUIRED")

    if not parsed.password:
        errors.append("DATABASE_PASSWORD_REQUIRED")

    return {
        "valid": not errors,
        "errors": errors,
        "host": parsed.hostname,
        "scheme": parsed.scheme,
    }


def validate_redis_url(
    redis_url: str,
    *,
    production: bool,
) -> dict:
    parsed = urlparse(redis_url)
    errors = []

    if parsed.scheme not in {"redis", "rediss"}:
        errors.append("REDIS_SCHEME_REQUIRED")

    if production and parsed.hostname in {
        "localhost",
        "127.0.0.1",
        None,
    }:
        errors.append("PRODUCTION_REDIS_HOST_REQUIRED")

    return {
        "valid": not errors,
        "errors": errors,
        "host": parsed.hostname,
        "scheme": parsed.scheme,
    }


def connector_fixture_violations(
    environment: dict[str, str],
    *,
    production: bool,
) -> list[str]:
    if not production:
        return []

    keys = (
        "AMAZON_CREATORS_FIXTURE_MODE",
        "EBAY_FIXTURE_MODE",
        "EBAY_BROWSE_FIXTURE_MODE",
        "IDEALO_FIXTURE_MODE",
    )

    return [
        key
        for key in keys
        if environment.get(key, "").lower() == "true"
    ]


def required_connector_credentials(
    environment: dict[str, str],
) -> dict[str, list[str]]:
    requirements = {
        "amazon": [
            "AMAZON_CREATORS_CLIENT_ID",
            "AMAZON_CREATORS_CLIENT_SECRET",
            "AMAZON_CREATORS_PARTNER_TAG",
        ],
        "ebay": [
            "EBAY_CLIENT_ID",
            "EBAY_CLIENT_SECRET",
        ],
        "idealo": [
            "IDEALO_PARTNER_ID",
            "IDEALO_API_KEY",
        ],
        "affiliate": [
            "AFFILIATE_NETWORK",
            "AFFILIATE_PUBLISHER_ID",
            "AFFILIATE_CAMPAIGN_ID",
        ],
    }

    return {
        connector: [
            key
            for key in keys
            if is_placeholder(environment.get(key))
        ]
        for connector, keys in requirements.items()
    }


def archive_exclusion_patterns() -> tuple[str, ...]:
    return (
        ".git/",
        ".venv/",
        ".pytest_cache/",
        ".ruff_cache/",
        "__pycache__/",
        ".env",
        ".env.",
        "dist/",
        "build/",
        ".test_workspaces/",
        # HARDEN-009: found via a real generated release ZIP, not assumed --
        # these two didn't exist when this exclusion list was first written,
        # so nothing ever added them. _arsiv/ (this session's archived RC
        # scripts/manifests/env backups, 158 files) and .claude/ (local
        # Claude Code tooling config) both leaked into a real sanitized
        # build until this fix.
        "_arsiv/",
        ".claude/",
        # HARDEN-009: also found via the real ZIP -- tests/runtime_tmp/ is
        # leftover state from previous test runs (a fake nested .env/.venv/
        # __pycache__/zip fixture tree used by test_rc58_release_hygiene_
        # scripts.py, plus an openapi snapshot). .gitignore/.dockerignore/
        # pyproject.toml's pytest norecursedirs already all recognize this
        # as scratch/generated content -- path_is_release_safe() just never
        # had it, so it shipped in a real generated release ZIP.
        "tests/runtime_tmp/",
        "tests/pytest_tmp/",
        "tests/.pytest_tmp/",
        "*.zip",
        "*.log",
    )


def path_is_release_safe(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    name = Path(normalized).name

    if normalized.startswith((
        ".git/",
        ".venv/",
        ".pytest_cache/",
        ".ruff_cache/",
        "dist/",
        "build/",
        ".test_workspaces/",
        # HARDEN-009 fix -- see archive_exclusion_patterns() comment above.
        "_arsiv/",
        ".claude/",
        "tests/runtime_tmp/",
        "tests/pytest_tmp/",
        "tests/.pytest_tmp/",
    )):
        return False

    if "/__pycache__/" in f"/{normalized}/":
        return False

    if name == ".env" or name.startswith(".env."):
        return (
            name.endswith(".example")
            or name == ".env.example"
        )

    if name.endswith((".pyc", ".pyo", ".log", ".zip")):
        return False

    return True


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sensitive_environment_keys(
    environment: dict[str, str],
) -> list[str]:
    return sorted(
        key
        for key in environment
        if any(
            part in key.upper()
            for part in SENSITIVE_NAME_PARTS
        )
    )


def redacted_environment(
    environment: dict[str, str],
) -> dict[str, str]:
    sensitive = set(sensitive_environment_keys(environment))
    return {
        key: (
            "<REDACTED>"
            if key in sensitive
            else value
        )
        for key, value in environment.items()
    }


def security_headers(
    *,
    production: bool,
) -> dict[str, str]:
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": (
            "camera=(), microphone=(), geolocation=()"
        ),
        "Cache-Control": "no-store",
        # HARDEN-004: this backend is a pure JSON API -- it never serves HTML,
        # inline scripts, or embeddable content -- so the CSP can be maximally
        # restrictive rather than needing per-deployment tuning.
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    }

    if production:
        headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    return headers


def route_auth_coverage(
    route_rows: list[dict],
) -> dict:
    write_methods = {"POST", "PUT", "PATCH", "DELETE"}
    public_count = 0
    protected_count = 0
    unprotected_write = []

    for row in route_rows:
        path = row["path"]
        methods = set(row.get("methods", []))
        protected = bool(row.get("protected"))

        if path in PUBLIC_PATHS:
            public_count += 1
            continue

        if protected:
            protected_count += 1
        elif methods & write_methods:
            unprotected_write.append({
                "path": path,
                "methods": sorted(methods & write_methods),
            })

    return {
        "public_count": public_count,
        "protected_count": protected_count,
        "unprotected_write_count": len(unprotected_write),
        "unprotected_write_routes": unprotected_write,
    }


def evaluate_environment(
    environment: dict[str, str],
) -> dict:
    production = (
        environment.get("APP_ENV", "local").lower()
        == "production"
    )

    jwt = secret_strength(
        environment.get("JWT_SECRET")
    )
    cors = validate_cors(
        parse_cors_origins(
            environment.get("CORS_ALLOWED_ORIGINS")
        ),
        production=production,
    )
    trusted_hosts = validate_trusted_hosts(
        parse_trusted_hosts(
            environment.get("TRUSTED_HOSTS")
        ),
        production=production,
    )
    database = validate_database_url(
        environment.get("DATABASE_URL", ""),
        production=production,
    )
    redis = validate_redis_url(
        environment.get("REDIS_URL", ""),
        production=production,
    )
    fixtures = connector_fixture_violations(
        environment,
        production=production,
    )

    checks = {
        "production": production,
        "debug_disabled": (
            not production
            or environment.get("DEBUG", "false").lower()
            == "false"
        ),
        "jwt": jwt,
        "cors": cors,
        "trusted_hosts": trusted_hosts,
        "database": database,
        "redis": redis,
        "fixture_violations": fixtures,
    }

    checks["ready"] = all((
        checks["debug_disabled"],
        jwt["valid"],
        cors["valid"],
        trusted_hosts["valid"],
        database["valid"],
        redis["valid"],
        not fixtures,
    ))

    return checks


def JSONResponse_payload(data: dict) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
    )
