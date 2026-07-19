from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc347_offer_normalization():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"))
    r=s.normalize_offer(product={"external_id":"A1"},raw_offer={"amount":10,"currency":"EUR"})
    assert r["price"]==10
