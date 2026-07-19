from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc349_error_mapping():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"))
    e=s.classify_error(status_code=429)
    assert e.retryable is True
    assert e.code=="AMAZON_RATE_LIMITED"
