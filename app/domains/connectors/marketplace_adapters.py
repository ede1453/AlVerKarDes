"""PARÇA B (CONNECT-004 devami, bkz. ADR-007): Amazon/eBay/Idealo icin
StoreConnector adaptorleri. Amac, uc connector'in da market.Price'a AYNI
paylasilan ingestion yolundan (ConnectorManager -> ConnectorIngestionService
-> POST /connectors/ingest, INTERNAL_SERVICE) yazmasi -- connector'a ozel
ayri bir yazma yolu olmamasi.

Her adaptor, ilgili *ConnectorService'in gercek (ya da fixture-mode)
ciktisini ConnectorProductResult'a esler ve is_real_data bayragini tasir.
"""

from __future__ import annotations

from typing import Any

from app.domains.amazon_connector.factory import build_amazon_connector
from app.domains.connectors.sdk import ConnectorProductResult, StoreConnector
from app.domains.marketplace_connectors.factory import (
    build_bestbuy_connector,
    build_ebay_connector,
    build_idealo_connector,
    configured_ebay_marketplace_ids,
    idealo_fixture_feed_content,
)


class AmazonStoreConnectorAdapter(StoreConnector):
    source_name = "amazon"

    async def search(self, query: str, country: str = "DE") -> list[ConnectorProductResult]:
        service = build_amazon_connector()
        result = service.search_products(keywords=query)

        results: list[ConnectorProductResult] = []
        for product in result["items"]:
            offers = product.get("offers") or []
            if not offers:
                continue
            offer = offers[0]
            results.append(
                ConnectorProductResult(
                    source="amazon",
                    title=product["title"],
                    url=product.get("detail_page_url"),
                    price=offer.get("price"),
                    currency=offer.get("currency", "EUR"),
                    availability=offer.get("availability"),
                    brand=product.get("brand"),
                    sku=product.get("external_id"),
                    raw=product,
                    confidence=80.0,
                    is_real_data=bool(product.get("is_real_data", False)),
                )
            )
        return results

    async def get_product(self, url: str) -> ConnectorProductResult:
        raise NotImplementedError(
            "amazon connector has no URL-keyed lookup API; only keyword search is supported"
        )


class EbayStoreConnectorAdapter(StoreConnector):
    # CONNECT-006: eBay'in Browse API'si tek base_url + degisen
    # X-EBAY-C-MARKETPLACE-ID header'iyla cok-ulkeli calisiyor (kod
    # incelemesiyle dogrulandi, ADR-008) -- her marketplace_id icin ayri
    # bir adaptor instance'i, source_name'i de ayirt edici (ebay_de/us/gb).
    def __init__(self, marketplace_id: str = "EBAY_DE"):
        self.marketplace_id = marketplace_id
        self.source_name = f"ebay_{marketplace_id.removeprefix('EBAY_').lower()}"

    async def search(self, query: str, country: str = "DE") -> list[ConnectorProductResult]:
        service = build_ebay_connector(marketplace_id=self.marketplace_id)
        result = service.search_items(query=query)

        return [
            ConnectorProductResult(
                source=self.source_name,
                title=item["title"],
                url=item.get("item_url"),
                price=item.get("price"),
                currency=item.get("currency", "EUR"),
                availability=item.get("condition"),
                sku=item.get("external_id"),
                raw=item.get("raw"),
                confidence=80.0,
                is_real_data=bool(item.get("is_real_data", False)),
            )
            for item in result["items"]
        ]

    async def get_product(self, url: str) -> ConnectorProductResult:
        raise NotImplementedError(
            "ebay connector has no URL-keyed lookup API; only keyword search is supported"
        )


class IdealoStoreConnectorAdapter(StoreConnector):
    source_name = "idealo"

    async def search(self, query: str, country: str = "DE") -> list[ConnectorProductResult]:
        service = build_idealo_connector()

        # Idealo is a periodic feed importer, not a live query API (see
        # ADR-007 "eBay/Idealo hazirlik durumu") -- there is no real-mode
        # equivalent of "search by keyword" without a feed already having
        # been ingested elsewhere. In fixture mode we can still demonstrate
        # the pluggable path end-to-end using the local sample feed. Like
        # the Amazon/eBay fixture transports, the sample feed's content
        # does not depend on `query` -- consistent behavior across all
        # three adapters in fixture mode, not Idealo-specific filtering.
        if not service.config.fixture_mode:
            return []

        content = idealo_fixture_feed_content()
        result = service.run_feed_collection(content=content, format="csv")

        return [
            ConnectorProductResult(
                source="idealo",
                title=offer["title"],
                url=offer.get("url"),
                price=offer.get("price"),
                currency=offer.get("currency", "EUR"),
                brand=offer.get("brand"),
                sku=offer.get("external_id"),
                raw=offer,
                confidence=75.0,
                is_real_data=bool(offer.get("is_real_data", False)),
            )
            for offer in result["offers"]
        ]

    async def get_product(self, url: str) -> ConnectorProductResult:
        raise NotImplementedError(
            "idealo connector has no URL-keyed lookup API; only feed-driven search is supported"
        )


class BestBuyStoreConnectorAdapter(StoreConnector):
    source_name = "bestbuy"

    async def search(self, query: str, country: str = "DE") -> list[ConnectorProductResult]:
        service = build_bestbuy_connector()
        result = service.search_products(keywords=query)

        return [
            ConnectorProductResult(
                source="bestbuy",
                title=item["title"],
                url=item.get("url"),
                price=item.get("price"),
                currency=item.get("currency", "USD"),
                availability=item.get("availability"),
                sku=item.get("external_id"),
                raw=item.get("raw"),
                confidence=80.0,
                is_real_data=bool(item.get("is_real_data", False)),
            )
            for item in result["items"]
        ]

    async def get_product(self, url: str) -> ConnectorProductResult:
        raise NotImplementedError(
            "bestbuy connector has no URL-keyed lookup API; only keyword search is supported"
        )


def build_live_connectors() -> list[StoreConnector]:
    ebay_connectors = [
        EbayStoreConnectorAdapter(marketplace_id=marketplace_id)
        for marketplace_id in configured_ebay_marketplace_ids()
    ]
    return [
        AmazonStoreConnectorAdapter(),
        *ebay_connectors,
        IdealoStoreConnectorAdapter(),
        BestBuyStoreConnectorAdapter(),
    ]
