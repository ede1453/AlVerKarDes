from __future__ import annotations

from pathlib import Path
import re


ROUTER_FILE = Path("app/api/v1/router.py")
CONFIG_FILE = Path("app/core/config.py")
ENV_EXAMPLE = Path(".env.example")


IMPORT_LINE = (
    "from app.api.v1.auth_core_router "
    "import router as auth_core_router"
)
INCLUDE_LINE = (
    "api_router.include_router(auth_core_router)"
)


def patch_router() -> None:
    text = ROUTER_FILE.read_text(
        encoding="utf-8"
    )

    text = re.sub(
        r"^from app\.api\.v1\.auth_core_router .*?\n",
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^api_router\.include_router\(\s*auth_core_router\s*\)\s*$",
        "",
        text,
        flags=re.MULTILINE,
    )

    marker = "api_router = APIRouter"
    index = text.find(marker)

    if index < 0:
        raise SystemExit(
            "Could not find api_router declaration."
        )

    text = (
        text[:index]
        + IMPORT_LINE
        + "\n"
        + text[index:]
    )
    text = text.rstrip() + "\n" + INCLUDE_LINE + "\n"

    ROUTER_FILE.write_text(
        text,
        encoding="utf-8",
    )


def patch_config() -> None:
    text = CONFIG_FILE.read_text(
        encoding="utf-8"
    )

    additions = {
        "JWT_ISSUER": (
            '    JWT_ISSUER: str = '
            '"ai-consumer-intelligence"'
        ),
        "JWT_AUDIENCE": (
            '    JWT_AUDIENCE: str = '
            '"ai-consumer-intelligence-api"'
        ),
        "REFRESH_TOKEN_EXPIRE_DAYS": (
            "    REFRESH_TOKEN_EXPIRE_DAYS: int = 30"
        ),
        "AUTH_SESSION_EXPIRE_DAYS": (
            "    AUTH_SESSION_EXPIRE_DAYS: int = 90"
        ),
        "AUTH_MAX_FAILED_ATTEMPTS": (
            "    AUTH_MAX_FAILED_ATTEMPTS: int = 5"
        ),
        "AUTH_LOCKOUT_MINUTES": (
            "    AUTH_LOCKOUT_MINUTES: int = 15"
        ),
    }

    anchor = "    ACCESS_TOKEN_EXPIRE_MINUTES"

    for key, line in additions.items():
        if key in text:
            continue

        lines = text.splitlines()
        insertion_index = next(
            (
                i + 1
                for i, value in enumerate(lines)
                if anchor in value
            ),
            len(lines),
        )
        lines.insert(insertion_index, line)
        text = "\n".join(lines) + "\n"

    CONFIG_FILE.write_text(
        text,
        encoding="utf-8",
    )


def patch_env_example() -> None:
    if not ENV_EXAMPLE.exists():
        return

    text = ENV_EXAMPLE.read_text(
        encoding="utf-8"
    )

    additions = """
JWT_ISSUER=ai-consumer-intelligence
JWT_AUDIENCE=ai-consumer-intelligence-api
REFRESH_TOKEN_EXPIRE_DAYS=30
AUTH_SESSION_EXPIRE_DAYS=90
AUTH_MAX_FAILED_ATTEMPTS=5
AUTH_LOCKOUT_MINUTES=15
"""

    if "JWT_ISSUER=" not in text:
        text = text.rstrip() + "\n\n" + additions.strip() + "\n"

    ENV_EXAMPLE.write_text(
        text,
        encoding="utf-8",
    )


def main() -> None:
    patch_router()
    patch_config()
    patch_env_example()
    print(
        "Authentication Core integration patch applied."
    )


if __name__ == "__main__":
    main()
