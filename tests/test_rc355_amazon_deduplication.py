from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc355_deduplication():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"))
    r=s.deduplicate_products(products=[{"asin":"A1"},{"asin":"A1"}])
    assert r["output_count"]==1
