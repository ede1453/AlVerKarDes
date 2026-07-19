from app.domains.marketplace_connectors.service import EbayBrowseConfig, EbayBrowseConnectorService


def test_rc376_ebay_ingestion():
    s=EbayBrowseConnectorService(
        EbayBrowseConfig(client_id="id",client_secret="secret",fixture_mode=True),
        http_transport=lambda **k:{"status_code":200,"json":{"itemSummaries":[]}},
    )
    assert s.build_ingestion_records([{"external_id":"1"}])["record_count"]==1
