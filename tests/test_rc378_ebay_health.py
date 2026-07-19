from app.domains.marketplace_connectors.service import EbayBrowseConfig, EbayBrowseConnectorService


def test_rc378_ebay_health():
    s=EbayBrowseConnectorService(
        EbayBrowseConfig(client_id="id",client_secret="secret",fixture_mode=True),
        http_transport=lambda **k:{"status_code":200,"json":{"itemSummaries":[]}},
    )
    assert s.health_check()["healthy"] is True
