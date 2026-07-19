import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import (
    TrustedHostMiddleware,
)
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.observability import ObservabilityMiddleware
from app.core.production_hardening import (
    evaluate_environment,
    parse_cors_origins,
    parse_trusted_hosts,
    secret_strength,
    security_headers,
    validate_cors,
    validate_request_body_limit,
    validate_trusted_hosts,
)
from app.core.security_middleware import (
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)


# HARDEN-007: evaluate_environment()'s "database"/"redis" checks (via
# validate_database_url()/validate_redis_url()) only ever parsed the URL
# string -- scheme, hostname, presence of credentials -- and never attempted
# a real connection. Confirmed live: stopping the actual Postgres container
# left GET /ready reporting "ready": true (database.valid: true) while every
# real DB-touching endpoint returned 500. These two probes make /ready
# reflect actual, current reachability instead of just config plausibility.


async def _check_database_reachable(*, timeout_seconds: float = 3.0, db_engine=None) -> bool:
    db_engine = engine if db_engine is None else db_engine
    try:
        async with asyncio.timeout(timeout_seconds):
            async with db_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _check_redis_reachable(
    *, timeout_seconds: float = 3.0, cache_backend: str | None = None, redis_url: str | None = None
) -> bool:
    cache_backend = settings.AICI_CACHE_BACKEND if cache_backend is None else cache_backend
    redis_url = settings.AICI_REDIS_URL if redis_url is None else redis_url

    if cache_backend != "redis":
        return True  # not applicable -- in-memory backend has nothing to reach

    def _ping() -> bool:
        import redis

        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=timeout_seconds,
            socket_timeout=timeout_seconds,
        )
        return bool(client.ping())

    try:
        return await asyncio.wait_for(asyncio.to_thread(_ping), timeout=timeout_seconds + 1)
    except Exception:
        return False


class WeakJwtSecretError(RuntimeError):
    """Raised at startup when APP_ENV=production but JWT_SECRET is weak/placeholder (HARDEN-001)."""


def enforce_jwt_secret_strength(*, app_env: str, jwt_secret: str | None) -> None:
    # HARDEN-001: secret_strength()/evaluate_environment() already existed and
    # were already unit-tested (production_hardening.py, test_rc434/435), but
    # nothing actually stopped the app from booting with a weak secret -- the
    # check was only reachable reactively via GET /ready. Confirmed live: the
    # running "production" container's JWT_SECRET was literally the
    # placeholder text "EN_AZ_32_KARAKTERLIK_GUCLU_RASTGELE_SECRET". This
    # makes the guard a real fail-fast startup gate instead of a pollable report.
    if app_env.lower() != "production":
        return

    result = secret_strength(jwt_secret)
    if not result["valid"]:
        raise WeakJwtSecretError(
            "JWT_SECRET is too weak for APP_ENV=production "
            f"(length={result['length']}, character_classes={result['character_classes']}; "
            "required: length>=32, character_classes>=3, not a placeholder value). "
            "Refusing to start. Set a strong JWT_SECRET before deploying."
        )


class WeakInternalServiceKeyError(RuntimeError):
    """Raised at startup when APP_ENV=production but INTERNAL_SERVICE_KEY is weak/placeholder (AUTH-004)."""


def enforce_internal_service_key_strength(*, app_env: str, internal_service_key: str | None) -> None:
    # AUTH-004 (ADR-006): same shape as HARDEN-001's JWT_SECRET guard --
    # secret_strength() is reused as-is rather than duplicated. Without this,
    # INTERNAL_SERVICE_KEY could ship as a weak/placeholder value the same
    # way JWT_SECRET once did, silently defeating the guard on all 93
    # INTERNAL_SERVICE endpoints.
    if app_env.lower() != "production":
        return

    result = secret_strength(internal_service_key)
    if not result["valid"]:
        raise WeakInternalServiceKeyError(
            "INTERNAL_SERVICE_KEY is too weak for APP_ENV=production "
            f"(length={result['length']}, character_classes={result['character_classes']}; "
            "required: length>=32, character_classes>=3, not a placeholder value). "
            "Refusing to start. Set a strong INTERNAL_SERVICE_KEY before deploying."
        )


class InvalidCorsConfigError(RuntimeError):
    """Raised at startup when APP_ENV=production but CORS_ALLOWED_ORIGINS is missing/insecure (HARDEN-002)."""


def enforce_cors_policy(*, app_env: str, cors_origins: list[str]) -> None:
    # HARDEN-002: validate_cors() already existed and was already unit-tested
    # (production_hardening.py, test_rc412/413/414), but like secret_strength()
    # before HARDEN-001, nothing enforced it -- create_app() just passed
    # whatever CORS_ALLOWED_ORIGINS held straight to CORSMiddleware, wildcard
    # or plain http:// included. This makes it a real fail-fast startup gate.
    if app_env.lower() != "production":
        return

    result = validate_cors(cors_origins, production=True)
    if not result["valid"]:
        raise InvalidCorsConfigError(
            "CORS_ALLOWED_ORIGINS is invalid for APP_ENV=production "
            f"(errors={result['errors']}; origins={result['origins']}). "
            "Production requires at least one well-formed HTTPS origin and no wildcard ('*'). "
            "Refusing to start. Set a valid CORS_ALLOWED_ORIGINS before deploying."
        )


class InvalidTrustedHostsConfigError(RuntimeError):
    """Raised at startup when APP_ENV=production but TRUSTED_HOSTS is missing/insecure (HARDEN-003)."""


def enforce_trusted_hosts_policy(*, app_env: str, trusted_hosts: list[str]) -> None:
    # HARDEN-003: same pattern as HARDEN-001/002. validate_trusted_hosts()
    # already existed and was already unit-tested (production_hardening.py,
    # test_rc415/416), but create_app() just skipped TrustedHostMiddleware
    # entirely whenever TRUSTED_HOSTS was unset (which it was in .env.prod --
    # identical gap to CORS before HARDEN-002) instead of refusing to start.
    if app_env.lower() != "production":
        return

    result = validate_trusted_hosts(trusted_hosts, production=True)
    if not result["valid"]:
        raise InvalidTrustedHostsConfigError(
            "TRUSTED_HOSTS is invalid for APP_ENV=production "
            f"(errors={result['errors']}; hosts={result['hosts']}). "
            "Production requires at least one trusted host and no wildcard ('*'). "
            "Refusing to start. Set a valid TRUSTED_HOSTS before deploying."
        )


REQUIRED_PRODUCTION_SECURITY_HEADERS = (
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Content-Security-Policy",
    "Referrer-Policy",
)


class MissingSecurityHeadersError(RuntimeError):
    """Raised at startup when APP_ENV=production but a required security header is missing (HARDEN-004)."""


def enforce_security_headers_policy(*, app_env: str, headers: dict[str, str]) -> None:
    # HARDEN-004: unlike CORS/TrustedHosts, security_headers() isn't driven by
    # an env var that can be left empty -- SecurityHeadersMiddleware is always
    # mounted. The real risk here is a code regression silently dropping a
    # required header (e.g. HSTS) from security_headers()'s output. This
    # guard makes that fail loudly at startup instead of shipping unnoticed.
    if app_env.lower() != "production":
        return

    missing = [name for name in REQUIRED_PRODUCTION_SECURITY_HEADERS if not headers.get(name)]
    if missing:
        raise MissingSecurityHeadersError(
            f"Missing required security headers for APP_ENV=production: {missing}. "
            "Refusing to start. Check security_headers() in production_hardening.py."
        )


class InvalidRequestBodyLimitError(RuntimeError):
    """Raised at startup when APP_ENV=production but MAX_REQUEST_BODY_BYTES is unsafe (HARDEN-005)."""


def enforce_request_body_limit_policy(*, app_env: str, maximum_bytes: int) -> None:
    # HARDEN-005: same shape as HARDEN-004 -- RequestSizeLimitMiddleware is
    # already always mounted with a sane default (2 MiB), so there's no
    # "silently disabled" gap. The real risk is a misconfigured *value*: zero
    # or negative effectively breaks all real traffic, and an accidental typo
    # (e.g. three extra zeros) could balloon the limit past any real
    # protection. validate_request_body_limit() is brand new for this guard
    # (no existing RC4xx validator covered this setting).
    if app_env.lower() != "production":
        return

    result = validate_request_body_limit(maximum_bytes, production=True)
    if not result["valid"]:
        raise InvalidRequestBodyLimitError(
            "MAX_REQUEST_BODY_BYTES is invalid for APP_ENV=production "
            f"(errors={result['errors']}; maximum_bytes={result['maximum_bytes']}). "
            f"Must be between {1024} and {50 * 1024 * 1024} bytes. "
            "Refusing to start. Set a sane MAX_REQUEST_BODY_BYTES before deploying."
        )


class DocsExposedInProductionError(RuntimeError):
    """Raised at startup when APP_ENV=production but interactive API docs/schema are still exposed (HARDEN-006)."""


def enforce_docs_disabled_policy(
    *, app_env: str, docs_url: str | None, redoc_url: str | None, openapi_url: str | None
) -> None:
    # HARDEN-006: same shape as HARDEN-004/005 -- docs_enabled's formula
    # (EXPOSE_API_DOCS and not production) already makes it impossible to
    # turn docs on in production via env vars alone (the `not production`
    # term always wins), so there's no external-config gap to validate here.
    # The real, found bug was different: openapi_url was hardcoded and never
    # gated by docs_enabled at all, silently exposing the full API schema
    # (every route, every field name) in production even with /docs and
    # /redoc correctly disabled. This guard is a regression safety net: if
    # anyone ever changes the docs_enabled formula (or re-hardcodes a URL
    # again), refuse to start rather than silently exposing it.
    if app_env.lower() != "production":
        return

    exposed = [
        name
        for name, url in (("docs_url", docs_url), ("redoc_url", redoc_url), ("openapi_url", openapi_url))
        if url
    ]
    if exposed:
        raise DocsExposedInProductionError(
            f"API docs/schema must be disabled for APP_ENV=production, but still exposed: {exposed}. "
            "Refusing to start."
        )


def create_app() -> FastAPI:
    enforce_jwt_secret_strength(
        app_env=settings.APP_ENV,
        jwt_secret=settings.JWT_SECRET,
    )
    enforce_internal_service_key_strength(
        app_env=settings.APP_ENV,
        internal_service_key=settings.INTERNAL_SERVICE_KEY,
    )
    enforce_cors_policy(
        app_env=settings.APP_ENV,
        cors_origins=parse_cors_origins(settings.CORS_ALLOWED_ORIGINS),
    )
    enforce_trusted_hosts_policy(
        app_env=settings.APP_ENV,
        trusted_hosts=parse_trusted_hosts(settings.TRUSTED_HOSTS),
    )
    enforce_request_body_limit_policy(
        app_env=settings.APP_ENV,
        maximum_bytes=settings.MAX_REQUEST_BODY_BYTES,
    )

    production = settings.APP_ENV.lower() == "production"
    enforce_security_headers_policy(
        app_env=settings.APP_ENV,
        headers=security_headers(production=production),
    )

    docs_enabled = (
        settings.EXPOSE_API_DOCS
        and not production
    )
    docs_url = "/docs" if docs_enabled else None
    redoc_url = "/redoc" if docs_enabled else None
    # HARDEN-006 fix: openapi_url was never gated by docs_enabled -- it was
    # hardcoded to "/openapi.json" unconditionally, so the full API schema
    # (every route, every request/response field name) was exposed in
    # production even though /docs and /redoc were correctly disabled.
    openapi_url = "/openapi.json" if docs_enabled else None

    enforce_docs_disabled_policy(
        app_env=settings.APP_ENV,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        version=settings.APP_VERSION,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    cors_origins = parse_cors_origins(
        settings.CORS_ALLOWED_ORIGINS
    )

    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "X-Correlation-ID",
                "Idempotency-Key",
            ],
        )

    trusted_hosts = parse_trusted_hosts(
        settings.TRUSTED_HOSTS
    )

    if trusted_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=trusted_hosts,
        )

    app.add_middleware(
        RequestSizeLimitMiddleware,
        maximum_bytes=settings.MAX_REQUEST_BODY_BYTES,
    )
    app.add_middleware(
        SecurityHeadersMiddleware,
        production=production,
    )
    app.add_middleware(ObservabilityMiddleware)

    @app.get("/", tags=["root"])
    async def root() -> dict:
        return {
            "status": "ok",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
            "health_url": "/health",
            "readiness_url": "/ready",
            # Restored from an older main.py revision (app/main---.py) where the
            # root route dropped these fields during the hardening rewrite.
            # docs_url reflects the real, current docs-disable-in-production
            # policy rather than unconditionally advertising a URL that 404s.
            "docs_url": "/docs" if docs_enabled else None,
            "release_health_url": "/api/v1/system/release-health",
        }

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {
            "status": "ok",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
        }

    @app.get("/live", tags=["health"])
    async def live() -> dict:
        return {"status": "alive"}

    @app.get("/ready", tags=["health"])
    async def ready() -> JSONResponse:
        result = evaluate_environment(
            {
                "APP_ENV": settings.APP_ENV,
                "DEBUG": str(settings.DEBUG),
                "DATABASE_URL": settings.DATABASE_URL,
                "REDIS_URL": settings.REDIS_URL,
                "JWT_SECRET": settings.JWT_SECRET,
                "CORS_ALLOWED_ORIGINS": (
                    settings.CORS_ALLOWED_ORIGINS
                ),
                "TRUSTED_HOSTS": settings.TRUSTED_HOSTS,
            }
        )

        # HARDEN-007: result["database"]/result["redis"] above are config-shape
        # checks only (URL parses correctly) -- they say nothing about whether
        # the database/cache are actually reachable right now. Add real probes
        # so /ready can't report "ready" while genuinely down.
        database_reachable = await _check_database_reachable()
        redis_reachable = await _check_redis_reachable()
        result["database"]["reachable"] = database_reachable
        result["redis"]["reachable"] = redis_reachable
        result["ready"] = result["ready"] and database_reachable and redis_reachable

        # HARDEN-007: this always returned HTTP 200 regardless of the "ready"
        # value in the body -- only a body-parsing consumer would ever notice
        # "not_ready". Naive consumers that check HTTP status alone (Docker
        # HEALTHCHECK, a plain `curl -f`, some load balancer health checks)
        # would treat every response as healthy. 503 is the conventional
        # "not ready to serve traffic" status for readiness probes.
        return JSONResponse(
            status_code=200 if result["ready"] else 503,
            content={
                "status": (
                    "ready"
                    if result["ready"]
                    else "not_ready"
                ),
                "checks": result,
            },
        )

    app.include_router(
        api_router,
        prefix="/api/v1",
    )

    # CLIENT-001 (ADR-010): minimal backend-verification frontend -- a
    # single static HTML file, no build step. Mounted under /ui (not "/",
    # which already serves the JSON root route above) so it can't shadow
    # any API surface. Same origin as the API, so no CORS config is needed
    # for it to call /api/v1/*.
    web_dir = Path(__file__).resolve().parent.parent / "web"
    if web_dir.is_dir():
        app.mount("/ui", StaticFiles(directory=web_dir, html=True), name="ui")

    return app


app = create_app()
