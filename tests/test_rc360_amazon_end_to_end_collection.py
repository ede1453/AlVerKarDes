from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc360_end_to_end_collection():
    payload={"items":[{"id":"A1","title":"Laptop","offers":[{"amount":700,"currency":"EUR"}]}]}
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret",fixture_mode=True),http_transport=lambda **k:{"status_code":200,"json":payload})
    r=s.run_collection(keywords="laptop")
    assert r["executed"] is True
    assert r["item_count"]==1
    assert r["snapshot_count"]==1
