from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.commerce_pipeline.service import (
    CommercePipelineService,
)

router = APIRouter(
    prefix="/commerce-pipeline",
    tags=["commerce-pipeline"],
)

_service = CommercePipelineService()


class PipelineRequest(BaseModel):
    marketplace: str
    items: list[dict[str, Any]] = Field(
        default_factory=list
    )
    target_currency: str = "EUR"
    exchange_rates: dict[str, float] = Field(
        default_factory=dict
    )
    reference_time: str | None = None
    user_id: str | None = None


@router.post("/clear")
def clear_pipeline():
    global _service
    _service = CommercePipelineService()
    return {"cleared": True}


@router.post("/run")
def run_pipeline(
    payload: PipelineRequest,
):
    return _service.run_pipeline(
        **payload.model_dump()
    )


@router.get("/runs")
def list_runs():
    return _service.list_runs()


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    run = _service.get_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="PIPELINE_RUN_NOT_FOUND",
        )

    return run
