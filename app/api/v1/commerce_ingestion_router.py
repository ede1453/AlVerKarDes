from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.commerce_ingestion.service import CommerceIngestionService

router = APIRouter(prefix="/commerce-ingestion", tags=["commerce-ingestion"])
_service = CommerceIngestionService()

class SourceRequest(BaseModel):
    source_id: str
    name: str
    source_type: str
    country: str
    currency: str
    enabled: bool = True
    trust_score: int = 50
    metadata: dict[str, Any] = Field(default_factory=dict)

class RawOfferRequest(BaseModel):
    source_id: str
    external_offer_id: str
    product_title: str
    product_url: str
    price: float
    currency: str
    availability: str = "unknown"
    seller_name: str | None = None
    observed_at: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)

class NormalizeRequest(BaseModel):
    raw_offer_id: str
    canonical_product_key: str | None = None

class SnapshotRequest(BaseModel):
    offer: dict[str, Any]

class RunStartRequest(BaseModel):
    source_id: str

class RunCompleteRequest(BaseModel):
    collected_count: int
    ingested_count: int
    failed_count: int = 0
    error: str | None = None

@router.post("/clear")
def clear_state():
    global _service
    _service = CommerceIngestionService()
    return {"cleared": True}

@router.post("/sources")
def register_source(payload: SourceRequest):
    return _service.register_source(**payload.model_dump())

@router.get("/sources")
def list_sources(enabled: bool | None = None, country: str | None = None):
    return _service.list_sources(enabled=enabled, country=country)

@router.post("/raw-offers")
def collect_raw_offer(payload: RawOfferRequest):
    return _service.collect_raw_offer(**payload.model_dump())

@router.post("/normalize")
def normalize(payload: NormalizeRequest):
    return _service.normalize_raw_offer(**payload.model_dump())

@router.post("/price-snapshots")
def ingest_snapshot(payload: SnapshotRequest):
    return _service.ingest_price_snapshot(payload.offer)

@router.post("/runs")
def start_run(payload: RunStartRequest):
    return _service.start_connector_run(payload.source_id)

@router.post("/runs/{run_id}/complete")
def complete_run(run_id: str, payload: RunCompleteRequest):
    return _service.complete_connector_run(run_id=run_id, **payload.model_dump())

@router.get("/sources/{source_id}/health")
def source_health(source_id: str):
    return _service.get_connector_health(source_id)
