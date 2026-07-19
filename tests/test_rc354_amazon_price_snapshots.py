from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc354_price_snapshots():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"))
    r=s.collect_price_snapshots(products=[{"external_id":"A1","offers":[{"price":10,"currency":"EUR"}]}])
    assert r["snapshot_count"]==1
