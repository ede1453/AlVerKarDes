from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc357_ingestion_records():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"))
    r=s.build_ingestion_records(products=[{"external_id":"A1","title":"X"}])
    assert r["record_count"]==1
