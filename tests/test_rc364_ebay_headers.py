from app.domains.marketplace_connectors.service import EbayBrowseConfig, EbayBrowseConnectorService


def test_rc364_ebay_headers():
    s=EbayBrowseConnectorService(
        EbayBrowseConfig(client_id="id",client_secret="secret",fixture_mode=True),
        http_transport=lambda **k:{"status_code":200,"json":{"itemSummaries":[]}},
    )
    assert s.build_headers("x")["X-EBAY-C-MARKETPLACE-ID"]=="EBAY_DE"
