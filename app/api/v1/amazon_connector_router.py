from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.amazon_connector.factory import build_amazon_connector
from app.domains.amazon_connector.service import (
    AmazonCreatorsConnectorService,
)
from app.core.internal_service_auth import require_internal_service_key
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter(
    prefix="/amazon-connector",
    tags=["amazon-connector"],
)


def get_amazon_connector() -> AmazonCreatorsConnectorService:
    return build_amazon_connector()


class SearchRequest(BaseModel):
    keywords: str
    page_size: int = 10
    page_token: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)


class ItemsRequest(BaseModel):
    identifiers: list[str]


@router.get("/health", operation_id="get_amazon_connector_health")
def health(
    service: AmazonCreatorsConnectorService = Depends(
        get_amazon_connector
    ),
):
    return service.health_check()


@router.get("/metrics", operation_id="get_amazon_connector_metrics")
def metrics(
    service: AmazonCreatorsConnectorService = Depends(
        get_amazon_connector
    ),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return service.metrics()


@router.post("/search", operation_id="search_amazon_products")
def search(
    payload: SearchRequest,
    service: AmazonCreatorsConnectorService = Depends(
        get_amazon_connector
    ),
):
    return service.search_products(
        keywords=payload.keywords,
        page_size=payload.page_size,
        page_token=payload.page_token,
        filters=payload.filters,
    )


@router.post("/items", operation_id="get_amazon_products")
def items(
    payload: ItemsRequest,
    service: AmazonCreatorsConnectorService = Depends(
        get_amazon_connector
    ),
):
    return service.get_products(
        identifiers=payload.identifiers
    )


@router.post("/collect", operation_id="collect_amazon_products")
def collect(
    payload: SearchRequest,
    service: AmazonCreatorsConnectorService = Depends(
        get_amazon_connector
    ),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return service.run_collection(
        keywords=payload.keywords,
        page_size=payload.page_size,
        filters=payload.filters,
    )
