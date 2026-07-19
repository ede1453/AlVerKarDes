from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc343_headers():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"))
    h=s.build_headers(access_token="abc",correlation_id="c1")
    assert h["Authorization"]=="Bearer abc"
    assert h["X-Correlation-ID"]=="c1"
