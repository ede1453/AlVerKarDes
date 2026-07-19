from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc348_response_normalization():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"))
    r=s.normalize_items_response({"items":[{"id":"A1","title":"X","offers":[]}]})
    assert r["item_count"]==1
