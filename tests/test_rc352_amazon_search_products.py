from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc352_search_products():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret",fixture_mode=True),http_transport=lambda **k:{"status_code":200,"json":{"items":[{"id":"A1","title":"X"}]}})
    assert s.search_products(keywords="x")["item_count"]==1
