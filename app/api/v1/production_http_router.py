
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.commerce_ingestion.http_execution import (
    FixtureHttpTransport,
    HttpResponse,
)
from app.domains.commerce_ingestion.production_http import (
    MultiPageConnectorRuntime,
)

router = APIRouter(
    prefix="/production-http",
    tags=["production-http"],
)

_transport = FixtureHttpTransport()
_runtime = MultiPageConnectorRuntime(
    _transport
)


class FixturePageRequest(BaseModel):
    url: str
    status_code: int = 200
    headers: dict[str, str] = Field(
        default_factory=lambda: {
            "content-type": "application/json"
        }
    )
    body: str
    elapsed_ms: float = 1.0


class MultiPageExecutionRequest(BaseModel):
    start_url: str
    base_headers: dict[str, str] = Field(
        default_factory=dict
    )
    timeout_seconds: int = 15
    max_pages: int = 10


@router.post("/clear")
def clear_production_http_state():
    global _transport, _runtime
    _transport = FixtureHttpTransport()
    _runtime = MultiPageConnectorRuntime(
        _transport
    )
    return {"cleared": True}


@router.post("/fixture-pages")
def register_fixture_page(
    payload: FixturePageRequest,
):
    _transport.responses[
        payload.url
    ] = HttpResponse(
        status_code=payload.status_code,
        headers=payload.headers,
        body=payload.body,
        elapsed_ms=payload.elapsed_ms,
    )
    return {"registered": True}


@router.post("/execute")
def execute_multi_page_connector(
    payload: MultiPageExecutionRequest,
):
    return _runtime.execute(
        **payload.model_dump()
    )
