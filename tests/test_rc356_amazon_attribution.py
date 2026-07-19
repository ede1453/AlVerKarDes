from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc356_attribution():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="mytag-21",client_id="id",client_secret="secret"))
    assert s.validate_attribution(detail_page_url="https://amazon.de/x?tag=mytag-21")["valid"] is True
