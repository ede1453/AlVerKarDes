from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.marketplace_connectors.service import (
    AffiliateAttributionService,
    AffiliateConfig,
    EbayBrowseConfig,
    EbayBrowseConnectorService,
    IdealoPartnerConfig,
    IdealoPartnerConnectorService,
)

router = APIRouter(prefix="/marketplace-connectors", tags=["marketplace-connectors"])

LEGACY_CONNECTORS = {
    "mock_marketplace": {"name":"mock_marketplace","available":True,"external":False},
    "amazon": {"name":"amazon","available":True,"external":True},
    "ebay": {"name":"ebay","available":True,"external":True},
    "idealo": {"name":"idealo","available":True,"external":True},
    "saturn": {"name":"saturn","available":True,"external":True},
    "mediamarkt": {"name":"mediamarkt","available":True,"external":True},
    "otto": {"name":"otto","available":True,"external":True},
}

class LegacyMarketplaceSearchRequest(BaseModel):
    query: str
    marketplace: str
    connector: str
    limit: int = 10

@router.get("", operation_id="list_marketplace_connectors")
def list_marketplace_connectors() -> dict[str, Any]:
    connectors = list(LEGACY_CONNECTORS.values())
    return {"connectors": connectors, "count": len(connectors)}

@router.post("/search", operation_id="search_marketplace_connector")
def search_marketplace_connector(payload: LegacyMarketplaceSearchRequest) -> dict[str, Any]:
    connector = LEGACY_CONNECTORS.get(payload.connector)
    if connector is None or payload.connector != "mock_marketplace":
        return {
            "status": "CONNECTOR_NOT_CONFIGURED",
            "executed": False,
            "connector": payload.connector,
            "marketplace": payload.marketplace,
            "external": True,
            "offer_count": 0,
            "offers": [],
            "query": payload.query,
        }

    offer_count = max(payload.limit, 0)
    offers = [
        {
            "offer_id": f"mock-offer-{index}",
            "external_id": f"mock-product-{index}",
            "marketplace": "mock_marketplace",
            "connector": "mock_marketplace",
            "product_name": payload.query,
            "title": payload.query,
            "price": 998.0 + index,
            "currency": "EUR",
            "shipping_cost": 0.0,
            "effective_price": 998.0 + index,
            "availability": "IN_STOCK",
            "condition": "NEW",
            "seller": "Mock Seller",
            "seller_name": "Mock Seller",
            "product_url": f"https://example.test/mock-marketplace/{index}",
            "url": f"https://example.test/mock-marketplace/{index}",
            "source_trust_score": 100,
            "external": False,
        }
        for index in range(1, offer_count + 1)
    ]

    return {
        "status": "COMPLETED",
        "executed": True,
        "connector": "mock_marketplace",
        "marketplace": "mock_marketplace",
        "external": False,
        "query": payload.query,
        "offer_count": len(offers),
        "offers": offers,
    }

def build_ebay_service():
    return EbayBrowseConnectorService(
        EbayBrowseConfig(client_id="fixture-client", client_secret="fixture-secret", fixture_mode=True),
        http_transport=lambda **_: {"status_code": 200, "json": {"itemSummaries": []}},
    )

def build_idealo_service():
    return IdealoPartnerConnectorService(
        IdealoPartnerConfig(partner_id="fixture-partner", api_key="fixture-key", fixture_mode=True)
    )

def build_affiliate_service():
    return AffiliateAttributionService(
        AffiliateConfig(
            network="internal",
            publisher_id="publisher-1",
            campaign_id="campaign-1",
            allowed_domains=("www.ebay.de", "www.idealo.de"),
        )
    )

class EbaySearchRequest(BaseModel):
    query: str
    limit: int = 50
    offset: int = 0
    category_ids: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)
    sort: str | None = None

class IdealoFeedRequest(BaseModel):
    content: str
    format: str = "csv"
    delimiter: str = ","

class AffiliateClickRequest(BaseModel):
    user_id: str
    deal_id: str
    destination_url: str

@router.get("/ebay/health", operation_id="get_ebay_connector_health")
def ebay_health():
    return build_ebay_service().health_check()

@router.post("/ebay/search", operation_id="search_ebay_browse_items")
def ebay_search(payload: EbaySearchRequest):
    return build_ebay_service().search_items(
        query=payload.query, limit=payload.limit, offset=payload.offset,
        category_ids=payload.category_ids, filters=payload.filters, sort=payload.sort,
    )

@router.get("/idealo/health", operation_id="get_idealo_connector_health")
def idealo_health():
    return build_idealo_service().health_check()

@router.post("/idealo/feed", operation_id="ingest_idealo_partner_feed")
def idealo_feed(payload: IdealoFeedRequest):
    return build_idealo_service().run_feed_collection(
        content=payload.content, format=payload.format, delimiter=payload.delimiter
    )

@router.post("/affiliate/click", operation_id="record_marketplace_affiliate_click")
def affiliate_click(payload: AffiliateClickRequest):
    return build_affiliate_service().record_click(
        user_id=payload.user_id, deal_id=payload.deal_id,
        destination_url=payload.destination_url,
    )

@router.get("/affiliate/readiness", operation_id="get_affiliate_connector_readiness")
def affiliate_readiness():
    return build_affiliate_service().readiness()
