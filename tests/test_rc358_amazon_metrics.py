from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc358_metrics():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"))
    assert s.metrics()["request_count"]==0
