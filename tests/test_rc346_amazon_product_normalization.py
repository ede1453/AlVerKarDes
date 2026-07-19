from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc346_product_normalization():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"))
    r=s.normalize_product({"id":"A1","title":"Laptop"})
    assert r["asin"]=="A1"
    assert r["title"]=="Laptop"
