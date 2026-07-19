from __future__ import annotations

from collections import Counter
from pathlib import Path

from fastapi.routing import APIRoute

from app.main import app


expected = [
    ("POST", "/api/v1/auth/refresh"),
    ("GET", "/api/v1/auth/sessions"),
    ("DELETE", "/api/v1/auth/sessions"),
    (
        "DELETE",
        "/api/v1/auth/sessions/{session_id}",
    ),
    (
        "POST",
        "/api/v1/auth/email-verification/issue",
    ),
    (
        "POST",
        "/api/v1/auth/email-verification/confirm",
    ),
    (
        "POST",
        "/api/v1/auth/password-reset/issue",
    ),
]

pairs = Counter(
    (method, route.path)
    for route in app.routes
    if isinstance(route, APIRoute)
    for method in route.methods or []
    if method not in {"HEAD", "OPTIONS"}
)

for pair in expected:
    if pairs[pair] != 1:
        raise SystemExit(
            f"Route count invalid: {pair} -> {pairs[pair]}"
        )

migration = Path(
    "alembic/versions/0015_authentication_core.py"
)

if not migration.exists():
    raise SystemExit(
        "Authentication Core migration is missing."
    )

print(
    "Authentication Core integration check passed."
)
