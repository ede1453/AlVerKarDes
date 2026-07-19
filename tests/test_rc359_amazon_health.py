from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc359_health():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"))
    assert s.health_check()["healthy"] is True
