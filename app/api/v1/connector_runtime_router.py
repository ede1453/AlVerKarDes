from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.commerce_ingestion.runtime import (
    ConnectorRuntimeService,
)

router = APIRouter(
    prefix="/connector-runtime",
    tags=["connector-runtime"],
)

_service = ConnectorRuntimeService()


class ConnectorExecutionRequest(BaseModel):
    source_id: str
    adapter_type: str
    source_config: dict[str, Any] = Field(
        default_factory=dict
    )
    canonical_product_key_field: str = (
        "canonical_product_key"
    )


@router.post("/clear")
def clear_connector_runtime():
    global _service
    _service = ConnectorRuntimeService()
    return {"cleared": True}


@router.post("/execute")
def execute_connector(
    payload: ConnectorExecutionRequest,
):
    return _service.execute_connector(
        source_id=payload.source_id,
        adapter_type=payload.adapter_type,
        source_config=payload.source_config,
        canonical_product_key_field=(
            payload.canonical_product_key_field
        ),
    )


@router.get("/runs/{run_id}")
def get_connector_run(run_id: str):
    run = _service.get_run(run_id)
    if run is None:
        raise HTTPException(
            status_code=404,
            detail="CONNECTOR_RUN_NOT_FOUND",
        )
    return run


@router.get("/events")
def list_connector_events(
    source_id: str | None = None,
    run_id: str | None = None,
):
    return _service.list_events(
        source_id=source_id,
        run_id=run_id,
    )


@router.get("/price-history/{canonical_product_key}")
def get_connector_price_history(
    canonical_product_key: str,
):
    return _service.price_bridge.get_history(
        canonical_product_key
    )
