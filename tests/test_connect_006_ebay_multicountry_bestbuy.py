"""CONNECT-006 (ADR-008): eBay çok-ülke desteği + yeni Best Buy connector'ı,
PARÇA B'nin paylaşılan ingestion yoluna (ConnectorManager ->
ConnectorIngestionService -> market.Price) bağlı.

eBay: EbayBrowseConfig.marketplace_id zaten çok-pazaryerli çalışıyordu (kod
incelemesiyle doğrulandı) -- yeni olan, aynı anda birden fazla marketplace_id
için ayrı connector instance'ı kurup TEK ingestion isteğinde hepsini
kullanabilmek (EBAY_ADDITIONAL_MARKETPLACES).

Best Buy: Amazon/eBay/Idealo'daki desenle birebir -- env-driven factory,
is_real_data, fixture-fallback, ConnectorError'ın yapılandırılmış HTTP
hatasına çevrilmesi.
"""

import os

from app.domains.connectors.marketplace_adapters import (
    BestBuyStoreConnectorAdapter,
    EbayStoreConnectorAdapter,
    build_live_connectors,
)
from app.domains.marketplace_connectors.factory import (
    build_bestbuy_connector,
    build_ebay_connector,
    configured_ebay_marketplace_ids,
)


def test_ebay_headers_differ_by_marketplace_id():
    from app.domains.marketplace_connectors.service import EbayBrowseConfig, EbayBrowseConnectorService

    headers_by_marketplace = {}
    for marketplace_id in ["EBAY_DE", "EBAY_US", "EBAY_GB"]:
        service = EbayBrowseConnectorService(
            EbayBrowseConfig(client_id="x", client_secret="y", marketplace_id=marketplace_id)
        )
        headers_by_marketplace[marketplace_id] = service.build_headers("fake-token")["X-EBAY-C-MARKETPLACE-ID"]

    assert headers_by_marketplace == {"EBAY_DE": "EBAY_DE", "EBAY_US": "EBAY_US", "EBAY_GB": "EBAY_GB"}
    assert len(set(headers_by_marketplace.values())) == 3


def test_configured_ebay_marketplace_ids_includes_additional(monkeypatch):
    monkeypatch.setenv("EBAY_MARKETPLACE_ID", "EBAY_DE")
    monkeypatch.setenv("EBAY_ADDITIONAL_MARKETPLACES", "EBAY_US, EBAY_GB")
    assert configured_ebay_marketplace_ids() == ["EBAY_DE", "EBAY_US", "EBAY_GB"]


def test_configured_ebay_marketplace_ids_deduplicates(monkeypatch):
    monkeypatch.setenv("EBAY_MARKETPLACE_ID", "EBAY_DE")
    monkeypatch.setenv("EBAY_ADDITIONAL_MARKETPLACES", "EBAY_DE,EBAY_US")
    assert configured_ebay_marketplace_ids() == ["EBAY_DE", "EBAY_US"]


async def test_ebay_fixture_mode_returns_distinct_data_per_marketplace(monkeypatch):
    monkeypatch.delenv("EBAY_CLIENT_ID", raising=False)
    monkeypatch.delenv("EBAY_CLIENT_SECRET", raising=False)

    results = {}
    for marketplace_id in ["EBAY_DE", "EBAY_US", "EBAY_GB"]:
        adapter = EbayStoreConnectorAdapter(marketplace_id=marketplace_id)
        items = await adapter.search(query="anything")
        assert items, f"{marketplace_id} returned no fixture data"
        results[marketplace_id] = items[0].title

    assert results == {
        "EBAY_DE": "Example Laptop",
        "EBAY_US": "Example Laptop US",
        "EBAY_GB": "Example Laptop UK",
    }
    assert len(set(results.values())) == 3


async def test_build_live_connectors_registers_one_ebay_adapter_per_marketplace(monkeypatch):
    monkeypatch.setenv("EBAY_MARKETPLACE_ID", "EBAY_DE")
    monkeypatch.setenv("EBAY_ADDITIONAL_MARKETPLACES", "EBAY_US,EBAY_GB")

    connectors = build_live_connectors()
    source_names = {connector.source_name for connector in connectors}
    assert {"ebay_de", "ebay_us", "ebay_gb", "amazon", "idealo", "bestbuy"} <= source_names


def test_build_bestbuy_connector_defaults_to_fixture_mode_without_credentials(monkeypatch):
    for key in ["BESTBUY_FIXTURE_MODE", "BESTBUY_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    service = build_bestbuy_connector()
    assert service.config.fixture_mode is True

    result = service.search_products(keywords="anything")
    assert result["item_count"] == 1
    assert result["items"][0]["is_real_data"] is False
    assert result["items"][0]["title"] == "Example Laptop"
    # Real Best Buy API returns sku as an int -- must be normalized to str
    # for OfferCreate.store_sku (live-caught bug, regression-tested here).
    assert isinstance(result["items"][0]["external_id"], str)


def test_build_bestbuy_connector_uses_real_mode_when_credentialed(monkeypatch):
    monkeypatch.delenv("BESTBUY_FIXTURE_MODE", raising=False)
    monkeypatch.setenv("BESTBUY_API_KEY", "real-looking-key")

    service = build_bestbuy_connector()
    assert service.config.fixture_mode is False


def test_build_bestbuy_connector_treats_change_me_as_missing(monkeypatch):
    monkeypatch.delenv("BESTBUY_FIXTURE_MODE", raising=False)
    monkeypatch.setenv("BESTBUY_API_KEY", "CHANGE_ME")

    service = build_bestbuy_connector()
    assert service.config.fixture_mode is True


async def test_bestbuy_adapter_tags_fixture_mode_results_not_real():
    adapter = BestBuyStoreConnectorAdapter()
    items = await adapter.search(query="anything")
    assert items
    assert all(item.is_real_data is False for item in items)
    assert isinstance(items[0].sku, str)
