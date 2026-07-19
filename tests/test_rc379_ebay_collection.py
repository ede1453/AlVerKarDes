from app.domains.marketplace_connectors.service import EbayBrowseConfig, EbayBrowseConnectorService


def test_rc379_ebay_collection():
    s=EbayBrowseConnectorService(
        EbayBrowseConfig(client_id="id",client_secret="secret",fixture_mode=True),
        http_transport=lambda **k:{"status_code":200,"json":{"itemSummaries":[]}},
    )
    assert s.run_collection(query="x")["executed"] is True
