
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.internal_service_auth import require_internal_service_key
from app.domains.commerce_ingestion.http_execution import (
    FixtureHttpTransport,
    HttpConnectorExecutionService,
    HttpResponse,
)

router = APIRouter(
    prefix="/http-connectors",
    tags=["http-connectors"],
)

_transport = FixtureHttpTransport()
_service = HttpConnectorExecutionService(_transport)


class RobotsPolicyRequest(BaseModel):
    domain: str
    allowed_paths: list[str] = Field(
        default_factory=lambda: ["/"]
    )
    disallowed_paths: list[str] = Field(
        default_factory=list
    )
    crawl_delay_seconds: int = 0


class FixtureResponseRequest(BaseModel):
    url: str
    status_code: int
    headers: dict[str, str] = Field(
        default_factory=dict
    )
    body: str = ""
    elapsed_ms: float = 1.0


class HttpExecutionRequest(BaseModel):
    connector_id: str
    url: str
    headers: dict[str, str] = Field(
        default_factory=dict
    )
    timeout_seconds: int = 15
    cache_ttl_seconds: int = 0


@router.post("/clear")
def clear_http_connector_state(
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    global _transport, _service
    _transport = FixtureHttpTransport()
    _service = HttpConnectorExecutionService(
        _transport
    )
    return {"cleared": True}


@router.post("/robots-policy")
def set_robots_policy(
    payload: RobotsPolicyRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.robots.set_policy(
        **payload.model_dump()
    )


@router.post("/fixture-responses")
def set_fixture_response(
    payload: FixtureResponseRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    _transport.responses[payload.url] = HttpResponse(
        status_code=payload.status_code,
        headers=payload.headers,
        body=payload.body,
        elapsed_ms=payload.elapsed_ms,
    )
    return {"registered": True}


@router.post("/execute")
def execute_http_connector(
    payload: HttpExecutionRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.execute(
        **payload.model_dump()
    )


@router.get("/sla/{connector_id}")
def get_connector_sla(
    connector_id: str,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.sla.get(connector_id)
