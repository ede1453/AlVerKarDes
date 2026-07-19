from app.domains.marketplace_connectors.service import EbayBrowseConfig, EbayBrowseConnectorService


def test_rc365_ebay_search_params():
    s=EbayBrowseConnectorService(
        EbayBrowseConfig(client_id="id",client_secret="secret",fixture_mode=True),
        http_transport=lambda **k:{"status_code":200,"json":{"itemSummaries":[]}},
    )
    assert s.build_search_params(query="laptop",limit=500)["limit"]==200
